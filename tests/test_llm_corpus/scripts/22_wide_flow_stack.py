"""22: Wide flow — 8 inputs feeding one STACK."""
import pandas as pd

ldn = pd.read_csv("trades_ldn.csv")
nyc = pd.read_csv("trades_nyc.csv")
sgp = pd.read_csv("trades_sgp.csv")
hkg = pd.read_csv("trades_hkg.csv")
tok = pd.read_csv("trades_tok.csv")
fra = pd.read_csv("trades_fra.csv")
syd = pd.read_csv("trades_syd.csv")
chi = pd.read_csv("trades_chi.csv")

# 8-input concat
all_trades = pd.concat([ldn, nyc, sgp, hkg, tok, fra, syd, chi], ignore_index=True)

all_trades.to_csv("trades_all_venues.csv", index=False)
