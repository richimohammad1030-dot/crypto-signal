//+------------------------------------------------------------------+
//| MomentumCandleXAU.mq5                                            |
//| Strategi Momentum Candle XAUUSD M5 (hasil backtest 13 Nov 2026)  |
//| Bodi >= $4 (400 pip), entry limit Fibo 23,6%, SL 74,5%,          |
//| TP ujung ekor candle, batal bila harga lari ke -100%,            |
//| tutup paksa 60 menit / 24:00 WIB. Risiko 1% per trade.           |
//| Notifikasi Telegram: sinyal, order terisi, posisi tutup, batal.  |
//+------------------------------------------------------------------+
#property copyright "Richi - Momentum Candle XAU"
#property version   "1.00"
#include <Trade/Trade.mqh>

input group "=== Strategi ==="
input double InpMinBody      = 4.00;   // Bodi minimal candle M5 (USD), $4 = 400 pip
input double InpBodyRatio    = 0.70;   // Bodi minimal dari panjang candle
input double InpMaxWickRatio = 0.10;   // Ekor searah maksimal dari panjang candle
input int    InpBreakBars    = 5;      // Close harus tembus high/low N candle sebelumnya
input double InpEntryFib     = 0.236;  // Level entry limit (Fibo)
input double InpSLFib        = 0.745;  // Level Stop Loss (Fibo)
input double InpTPFib        = 0.0;    // Level TP (0 = ujung ekor candle momentum)
input double InpCancelFib    = -1.0;   // Order batal bila harga menyentuh level ini dulu
input int    InpMaxHoldMin   = 60;     // Umur posisi maksimal (menit)

input group "=== Risiko ==="
input double InpRiskPct      = 1.0;    // Risiko per trade (% balance)

input group "=== Jam aktif (WIB) ==="
input int    InpServerGMT    = 0;      // Selisih jam server broker dari GMT (Exness = 0)
input int    InpStartWIB     = 7;      // Mulai cari sinyal (jam WIB)
input int    InpEndWIB       = 24;     // Semua order/posisi ditutup (jam WIB, 24 = tengah malam)

input group "=== Telegram ==="
input string InpTgToken      = "";     // Token bot Telegram
input string InpTgChatId     = "";     // Chat ID / channel ID (mis. -100xxxxxxxxxx)
input string InpTag          = "⚡ MOMENTUM M5"; // Penanda pesan (beda dari bot XAU harian)

input group "=== Lain-lain ==="
input long   InpMagic        = 260501; // Magic number EA ini

CTrade   trade;
datetime gLastBar = 0;

//------------------------------------------------------------------ util waktu
int WibHour(datetime serverTime)
{
   MqlDateTime s;
   TimeToStruct(serverTime - InpServerGMT * 3600 + 7 * 3600, s);
   return s.hour;
}
bool InSession(datetime serverTime)
{
   int h = WibHour(serverTime);
   return (h >= InpStartWIB && h < InpEndWIB);
}

//------------------------------------------------------------------ Telegram
string UrlEncode(const string text)
{
   uchar b[];
   int n = StringToCharArray(text, b, 0, WHOLE_ARRAY, CP_UTF8) - 1;
   string out = "";
   for(int i = 0; i < n; i++)
   {
      uchar c = b[i];
      if((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
         c == '-' || c == '_' || c == '.' || c == '~')
         out += CharToString(c);
      else
         out += StringFormat("%%%02X", c);
   }
   return out;
}

void TgSend(string text)
{
   Print(text);
   if(InpTgToken == "" || InpTgChatId == "") return;
   if(MQLInfoInteger(MQL_TESTER)) return;              // WebRequest tidak jalan di Strategy Tester
   string url  = "https://api.telegram.org/bot" + InpTgToken + "/sendMessage";
   string body = "chat_id=" + UrlEncode(InpTgChatId) + "&parse_mode=HTML&text=" + UrlEncode(InpTag + "\n" + text);
   char data[], res[];
   StringToCharArray(body, data, 0, StringLen(body));  // body sudah ASCII (hasil URL encode)
   string resHeaders;
   ResetLastError();
   int code = WebRequest("POST", url, "Content-Type: application/x-www-form-urlencoded\r\n", 5000, data, res, resHeaders);
   if(code != 200)
      Print("Telegram gagal, kode=", code, " error=", GetLastError(),
            " (pastikan https://api.telegram.org ada di Tools > Options > Expert Advisors > Allow WebRequest)");
}

string Px(double p) { return DoubleToString(p, _Digits); }

//------------------------------------------------------------------ hitung posisi/order milik EA
int MyPositions()
{
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t > 0 && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagic) n++;
   }
   return n;
}
int MyOrders()
{
   int n = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t > 0 && OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == InpMagic) n++;
   }
   return n;
}

//------------------------------------------------------------------ ukuran lot dari risiko
double CalcLot(double entry, double sl)
{
   double riskMoney = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiskPct / 100.0;
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tickValue <= 0) tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double dist = MathAbs(entry - sl);
   if(tickSize <= 0 || tickValue <= 0 || dist <= 0) return 0;
   double lossPerLot = dist / tickSize * tickValue;
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lot  = MathFloor(riskMoney / lossPerLot / step) * step;
   if(lot < vmin)
   {
      PrintFormat("Lot hitungan %.4f < minimal %.2f, dipakai lot minimal (risiko nyata %.2f%%)",
                  lot, vmin, vmin * lossPerLot / AccountInfoDouble(ACCOUNT_BALANCE) * 100.0);
      lot = vmin;
   }
   return MathMin(lot, vmax);
}

//------------------------------------------------------------------ tutup semua milik EA
void CloseAll(string reason)
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t > 0 && OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == InpMagic)
         if(trade.OrderDelete(t)) TgSend("❌ Order limit dibatalkan (" + reason + ")");
   }
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t > 0 && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagic)
         trade.PositionClose(t);                       // notifikasi hasil dikirim di OnTradeTransaction
   }
}

//------------------------------------------------------------------ order limit: batal bila harga lari
void ManagePending()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t == 0 || OrderGetString(ORDER_SYMBOL) != _Symbol || OrderGetInteger(ORDER_MAGIC) != InpMagic) continue;
      string cm = OrderGetString(ORDER_COMMENT);       // format: MC|cx=<level batal>
      int k = StringFind(cm, "cx=");
      if(k < 0) continue;
      double cx = StringToDouble(StringSubstr(cm, k + 3));
      long type = OrderGetInteger(ORDER_TYPE);
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      bool hit = (type == ORDER_TYPE_BUY_LIMIT && bid >= cx) || (type == ORDER_TYPE_SELL_LIMIT && ask <= cx);
      if(hit && trade.OrderDelete(t))
         TgSend("❌ Order limit dibatalkan: harga sudah lari ke " + Px(cx) + " sebelum terisi");
   }
}

//------------------------------------------------------------------ posisi: tutup paksa setelah umur maksimal
void ManagePositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
      if(TimeCurrent() - opened >= InpMaxHoldMin * 60) trade.PositionClose(t);
   }
}

//------------------------------------------------------------------ deteksi momentum candle (candle M5 terakhir yang sudah close)
void CheckSignal()
{
   datetime barTime = iTime(_Symbol, PERIOD_M5, 1);
   if(!InSession(barTime) || !InSession(TimeCurrent())) return;
   if(MyPositions() > 0 || MyOrders() > 0) return;      // 1 posisi pada satu waktu, tanpa layering

   double o = iOpen(_Symbol, PERIOD_M5, 1), h = iHigh(_Symbol, PERIOD_M5, 1);
   double l = iLow(_Symbol, PERIOD_M5, 1),  c = iClose(_Symbol, PERIOD_M5, 1);
   double rng = h - l, body = MathAbs(c - o);
   if(rng <= 0 || body < InpMinBody || body < InpBodyRatio * rng) return;

   int hi = iHighest(_Symbol, PERIOD_M5, MODE_HIGH, InpBreakBars, 2);
   int lo = iLowest(_Symbol, PERIOD_M5, MODE_LOW, InpBreakBars, 2);
   if(hi < 0 || lo < 0) return;
   double prevH = iHigh(_Symbol, PERIOD_M5, hi), prevL = iLow(_Symbol, PERIOD_M5, lo);

   int dir = 0;
   if(c > o && (h - c) <= InpMaxWickRatio * rng && c > prevH) dir = 1;
   if(c < o && (c - l) <= InpMaxWickRatio * rng && c < prevL) dir = -1;
   if(dir == 0) return;

   double tip   = (dir == 1) ? h : l;                  // ujung candle searah tren = Fibo 0
   double entry = NormalizeDouble(tip - dir * InpEntryFib  * rng, _Digits);
   double sl    = NormalizeDouble(tip - dir * InpSLFib     * rng, _Digits);
   double tp    = NormalizeDouble(tip - dir * InpTPFib     * rng, _Digits);
   double cx    = NormalizeDouble(tip - dir * InpCancelFib * rng, _Digits);

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double stopLvl = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
   if((dir == 1 && bid >= cx) || (dir == -1 && ask <= cx)) return;  // sudah lari sebelum sempat dipasang

   bool market = (dir == 1 && ask <= entry) || (dir == -1 && bid >= entry);
   double refEntry = market ? (dir == 1 ? ask : bid) : entry;
   if(MathAbs(refEntry - sl) < stopLvl || MathAbs(tp - refEntry) < stopLvl) return;
   if((tp - refEntry) * dir <= 0) return;

   double lot = CalcLot(refEntry, sl);
   if(lot <= 0) return;
   string cm = "MC|cx=" + Px(cx);
   bool ok;
   if(market) ok = (dir == 1) ? trade.Buy(lot, _Symbol, 0, sl, tp, cm) : trade.Sell(lot, _Symbol, 0, sl, tp, cm);
   else       ok = (dir == 1) ? trade.BuyLimit(lot, entry, _Symbol, sl, tp, ORDER_TIME_GTC, 0, cm)
                              : trade.SellLimit(lot, entry, _Symbol, sl, tp, ORDER_TIME_GTC, 0, cm);
   if(!ok) { Print("Order gagal: ", trade.ResultRetcodeDescription()); return; }

   string arah = (dir == 1) ? "🟢 BUY" : "🔴 SELL";
   TgSend(StringFormat("%s %s %s\nMomentum candle M5 bodi $%.2f\nEntry: %s\nSL: %s\nTP: %s\nLot: %.2f (risiko %.1f%%)\nBatal bila harga ke %s",
          arah, market ? "MARKET" : "LIMIT", _Symbol, body, Px(refEntry), Px(sl), Px(tp), lot, InpRiskPct, Px(cx)));
}

//------------------------------------------------------------------ event MT5
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(50);
   if(_Period != PERIOD_M5) Print("Catatan: EA membaca candle M5 apa pun timeframe chart-nya.");
   TgSend("✅ EA Momentum Candle aktif di " + _Symbol);
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if(!InSession(TimeCurrent()))
   {
      if(MyPositions() > 0 || MyOrders() > 0) CloseAll("tutup harian 24:00 WIB");
      return;
   }
   ManagePending();
   ManagePositions();
   datetime bar0 = iTime(_Symbol, PERIOD_M5, 0);
   if(bar0 != gLastBar)
   {
      gLastBar = bar0;
      CheckSignal();
   }
}

void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &req, const MqlTradeResult &res)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagic) return;
   if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) != _Symbol) return;

   long   entry  = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   long   type   = HistoryDealGetInteger(trans.deal, DEAL_TYPE);
   double price  = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
   double vol    = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);

   if(entry == DEAL_ENTRY_IN)
   {
      TgSend(StringFormat("📥 Posisi %s terbuka di %s (lot %.2f)", type == DEAL_TYPE_BUY ? "BUY" : "SELL", Px(price), vol));
   }
   else if(entry == DEAL_ENTRY_OUT)
   {
      double pl = HistoryDealGetDouble(trans.deal, DEAL_PROFIT) + HistoryDealGetDouble(trans.deal, DEAL_SWAP)
                + HistoryDealGetDouble(trans.deal, DEAL_COMMISSION);
      long reason = HistoryDealGetInteger(trans.deal, DEAL_REASON);
      string why = (reason == DEAL_REASON_TP) ? "🎯 TP kena" : (reason == DEAL_REASON_SL) ? "🛑 SL kena" : "⏱ Ditutup EA (batas waktu)";
      double bal = AccountInfoDouble(ACCOUNT_BALANCE);
      TgSend(StringFormat("%s di %s\nHasil: %+.2f %s (%+.2f%%)", why, Px(price), pl,
             AccountInfoString(ACCOUNT_CURRENCY), bal > 0 ? pl / (bal - pl) * 100.0 : 0.0));
   }
}
//+------------------------------------------------------------------+
