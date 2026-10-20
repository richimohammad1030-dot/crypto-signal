"""Uji walk-forward: model ML vs label 4 faktor. Bisa dipakai sebagai modul: walkforward(df) -> (per_tahun, ringkasan).
Setiap tahun uji Y: model dilatih hanya dengan trade yang SELESAI sebelum 1 Jan Y, lalu menilai trade yang dibuka di Y.
Skor dibagi tiga kelompok memakai batas tertile dari data latih (sama seperti label HIGH/MEDIUM/LOW).
Argumen: <trades_scored.pkl>"""
import sys, warnings
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression, HuberRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from scipy.stats import spearmanr
warnings.filterwarnings("ignore")

FEATS = ["trend", "ext", "dist", "slpct", "mom20", "slope", "breadth", "rank", "btc", "is_short", "fund0"]

def _prep(df):
    df = df[df.year >= 2020].reset_index(drop=True).copy()
    df["is_short"] = (df.d == -1).astype(int)
    df["fund0"] = df["fund"].fillna(0.0)
    df["Rc"] = df.R.clip(upper=10)          # batasi outlier untuk target regresi
    df["win"] = (df.R > 0).astype(int)
    return df

def models():
    return {
        "Logistik (menang/kalah)": ("clf", make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=2000))),
        "Huber (prediksi R)": ("reg", make_pipeline(StandardScaler(), HuberRegressor(alpha=1.0, max_iter=2000))),
        "Pohon dangkal (prediksi R)": ("reg", HistGradientBoostingRegressor(max_depth=2, learning_rate=0.05, max_iter=150,
                                                                       min_samples_leaf=60, l2_regularization=1.0)),
        "Pohon dangkal (menang/kalah)": ("clf", HistGradientBoostingClassifier(max_depth=2, learning_rate=0.05, max_iter=150,
                                                                           min_samples_leaf=60, l2_regularization=1.0)),
    }

def label_wf(train, test):
    """Label 4 faktor dengan batas tertile dihitung ulang HANYA dari data latih (versi walk-forward yang adil)."""
    def pts(col, low_good=True):
        a, b = np.quantile(train[col], [1 / 3, 2 / 3])
        s = np.where(test[col] < a, 1, np.where(test[col] > b, -1, 0))
        return s if low_good else -s
    return pts("slpct") + pts("ext") + pts("rank") + test.btc.values

def walkforward(df, first_test_year=2022):
  df = _prep(df)
  rows, per_year = [], []
  last = int(df.year.max())
  for Y in range(first_test_year, last + 1):
      t0 = pd.Timestamp(f"{Y}-01-01").timestamp()
      train = df[df.t1 < t0]; test = df[(df.t0 >= t0) & (df.t0 < pd.Timestamp(f"{Y + 1}-01-01").timestamp())]
      scores = {"Label 4 faktor (sekarang)": test.score.values,
                "Label 4 faktor (batas walk-forward)": label_wf(train, test)}
      tr_scores = {"Label 4 faktor (sekarang)": train.score.values, "Label 4 faktor (batas walk-forward)": label_wf(train, train)}
      for name, (kind, m) in models().items():
          y = train.win if kind == "clf" else train.Rc
          m.fit(train[FEATS], y)
          f = (lambda X: m.predict_proba(X)[:, 1]) if kind == "clf" else m.predict
          scores[name], tr_scores[name] = f(test[FEATS]), f(train[FEATS])
      for name, s in scores.items():
          if name.startswith("Label"):
              grp = np.where(s >= 2, 2, np.where(s <= -1, 0, 1))      # sama dengan aturan HIGH/MEDIUM/LOW
          else:
              a, b = np.quantile(tr_scores[name], [0.30, 0.70])       # porsi ±30/40/30 seperti label sekarang
              grp = np.digitize(s, [a, b])
          R = test.R.values
          rows.append(dict(model=name, year=Y, n=len(test), high=R[grp == 2].mean(), mid=R[grp == 1].mean(),
                           low=R[grp == 0].mean(), nh=(grp == 2).sum(), nl=(grp == 0).sum(),
                           rho=spearmanr(s, R).correlation, skip_low=R[grp != 0].sum() - R.sum()))
      per_year.append((Y, len(train), len(test)))

  res = pd.DataFrame(rows)
  agg = res.groupby("model").apply(lambda g: pd.Series(dict(
      high_R=np.average(g.high, weights=g.nh), low_R=np.average(g.low, weights=g.nl),
      selisih=np.average(g.high, weights=g.nh) - np.average(g.low, weights=g.nl),
      tahun_high_menang=int((g.high > g.low).sum()), tahun_uji=len(g))), include_groups=False).sort_values("selisih", ascending=False)
  return res, agg

if __name__ == "__main__":
    d = pd.read_pickle(sys.argv[1])
    res, agg = walkforward(d)
    pd.set_option("display.width", 220); pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
    print(res.pivot_table(index="model", columns="year", values=["high", "low"]).round(2)); print(agg)
