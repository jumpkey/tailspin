#!/usr/bin/env python3
"""
45_plot_exec_storyline.py — Plain-language executive charts (one message each).

Renders the story set approved in reports/CHART_SPECS_DRAFT.md to output/exec/.
No data-science vocabulary on any chart: titles ARE the takeaway sentence, axes
are plain English, <=3 colors, large fonts, source/repro footer.

Sources:
  - data/curated/hubspoke_operator_fact_2026/  (carve-out fact: 2024-Apr2026,
    period_flag baseline=2024-25 / recent=2026)  -> A1, A2, A3
  - output/fragility_v_hotspot_scorecard.parquet (committed 2024-25 scorecard) -> B1, B2

Usage:  python scripts/45_plot_exec_storyline.py
"""
import os
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "exec"
OUT.mkdir(parents=True, exist_ok=True)

CARVE = str(ROOT / "data/curated/hubspoke_operator_fact_2026/**/*.parquet")
SCORE = str(ROOT / "output/fragility_v_hotspot_scorecard.parquet/**/*.parquet")
REPO = "[repository URL]"
FOOT = "Source: U.S. DOT BTS On-Time data + NOAA weather, Jan 2024 - Apr 2026.  Reproducible: " + REPO

# Consistent, restrained palette
C_PSA   = "#C0392B"   # red  = the problem operator
C_ENVOY = "#2E86C1"   # blue = the clean operator
C_SKY   = "#7F8C8D"   # gray = neutral
C_PRIOR = "#95A5A6"   # gray = past
C_NOW   = "#C0392B"   # red  = current
C_FLT   = "#AAB7B8"   # light gray = share of flights
C_BAD   = "#C0392B"   # red = share of worst

OP_LABEL = {"PSA_operated":"American Eagle\n- PSA",
            "Envoy_operated":"American Eagle\n- Envoy",
            "SkyWest_unresolved":"American Eagle\n- SkyWest"}
OP_COLOR = {"PSA_operated":C_PSA,"Envoy_operated":C_ENVOY,"SkyWest_unresolved":C_SKY}
WX_LABEL = {"benign":"Good\nweather","marginal":"Marginal","adverse":"Bad\nweather"}

plt.rcParams.update({
    "font.size": 15, "axes.titlesize": 21, "axes.titleweight": "bold",
    "axes.labelsize": 15, "figure.dpi": 130, "axes.spines.top": False,
    "axes.spines.right": False, "font.family": "DejaVu Sans",
})

con = duckdb.connect()

def footer(fig):
    fig.text(0.5, 0.015, FOOT, ha="center", va="bottom", fontsize=9, color="#666")

def disruption_expr():
    # cancelled OR arrival 60+ min late, over all scheduled flights
    return "avg((CAST(cancelled_flag AS INT)=1 OR CAST(severe_delay_flag AS INT)=1)::INT)"


def chart_A1():
    df = con.sql(f"""
      SELECT operator_class, weather_bucket, {disruption_expr()} rate, count(*) n
      FROM read_parquet('{CARVE}', hive_partitioning=1)
      WHERE hub_family='DFW' AND (origin='LFT' OR dest='LFT')
        AND period_flag='baseline' AND weather_bucket IN ('benign','marginal','adverse')
      GROUP BY 1,2
    """).df()
    ops = ["PSA_operated","Envoy_operated","SkyWest_unresolved"]
    wx = ["benign","marginal","adverse"]
    fig, ax = plt.subplots(figsize=(12.5,6.8))
    import numpy as np
    x = np.arange(len(wx)); w = 0.26
    for i,op in enumerate(ops):
        vals=[float(df[(df.operator_class==op)&(df.weather_bucket==b)].rate.values[0])
              if len(df[(df.operator_class==op)&(df.weather_bucket==b)]) else 0 for b in wx]
        bars=ax.bar(x+(i-1)*w, vals, w, label=OP_LABEL[op].replace("\n"," "), color=OP_COLOR[op])
        for b,v in zip(bars,vals):
            ax.text(b.get_x()+b.get_width()/2, v+0.006, f"{v*100:.0f}%", ha="center", fontsize=12, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([WX_LABEL[b] for b in wx])
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylabel("Flights cancelled or delayed 1+ hour")
    ax.set_title("When the weather turns, the DFW-Lafayette schedule breaks", pad=16, fontsize=18)
    ax.legend(loc="upper left", frameon=False, fontsize=12)
    ax.set_ylim(0, max(0.45, ax.get_ylim()[1]))
    ax.annotate("Envoy degrades most\nin bad weather (~4x)", xy=(2.0,0.30), xytext=(1.05,0.40),
                fontsize=11, color=C_ENVOY, ha="center",
                arrowprops=dict(arrowstyle="->",color=C_ENVOY))
    ax.text(0.99,0.97,"DFW-Lafayette, 2024-2025", transform=ax.transAxes, ha="right", va="top",
            fontsize=11, style="italic", color="#555")
    footer(fig); fig.tight_layout(rect=[0,0.04,1,1])
    fig.savefig(OUT/"A1_weather_breaks_schedule.png"); plt.close(fig)


def chart_A2():
    df = con.sql(f"""
      SELECT year_month ym, operator_class, count(*) n
      FROM read_parquet('{CARVE}', hive_partitioning=1)
      WHERE hub_family='DFW' AND (origin='LFT' OR dest='LFT')
        AND operator_class IN ('PSA_operated','Envoy_operated','SkyWest_unresolved')
      GROUP BY 1,2 ORDER BY 1
    """).df()
    piv = df.pivot_table(index="ym",columns="operator_class",values="n",aggfunc="sum",fill_value=0).sort_index()
    fig, ax = plt.subplots(figsize=(13,6.6))
    bottom=None
    import numpy as np
    months=list(piv.index)
    for op in ["PSA_operated","Envoy_operated","SkyWest_unresolved"]:
        vals=piv[op].values if op in piv else np.zeros(len(months))
        ax.bar(months, vals, bottom=bottom, label=OP_LABEL[op].replace("\n"," "), color=OP_COLOR[op])
        bottom = vals if bottom is None else bottom+vals
    ax.set_ylabel("Flights per month")
    ax.set_title("The operator on your route keeps changing - and it's PSA now", pad=16)
    step=max(1,len(months)//12)
    ax.set_xticks(range(0,len(months),step)); ax.set_xticklabels(months[::step], rotation=45, ha="right", fontsize=10)
    ax.legend(loc="upper left", frameon=False, fontsize=12, ncol=3)
    ax.axvspan(len(months)-4.5, len(months)-0.5, color="#F9E79F", alpha=0.35, zorder=0)
    ax.text(len(months)-2.5, ax.get_ylim()[1]*0.92, "2026: ~90% PSA\n(Envoy nearly gone)", ha="center", fontsize=11, color=C_PSA, fontweight="bold")
    footer(fig); fig.tight_layout(rect=[0,0.04,1,1])
    fig.savefig(OUT/"A2_operator_keeps_changing.png"); plt.close(fig)


def chart_A3():
    df = con.sql(f"""
      SELECT CASE WHEN year(flight_date)=2026 THEN '2026' ELSE '2024-2025' END season,
             {disruption_expr()} rate, count(*) n
      FROM read_parquet('{CARVE}', hive_partitioning=1)
      WHERE hub_family='DFW' AND (origin='LFT' OR dest='LFT')
        AND month(flight_date) BETWEEN 1 AND 4
      GROUP BY 1
    """).df().set_index("season")
    order=["2024-2025","2026"]
    vals=[float(df.loc[s,"rate"]) for s in order]; ns=[int(df.loc[s,"n"]) for s in order]
    fig, ax = plt.subplots(figsize=(8.5,6.6))
    bars=ax.bar(order, vals, color=[C_PRIOR,C_NOW], width=0.55)
    for b,v,nn in zip(bars,vals,ns):
        ax.text(b.get_x()+b.get_width()/2, v+0.004, f"{v*100:.1f}%", ha="center", fontsize=15, fontweight="bold")
        ax.text(b.get_x()+b.get_width()/2, 0.004, f"{nn:,} flights", ha="center", fontsize=10, color="white", va="bottom")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylabel("Flights cancelled or delayed 1+ hour")
    ax.set_title("Is 2026 any better? No.", pad=16)
    ax.set_ylim(0, max(vals)*1.35)
    ax.text(0.5,0.99,"DFW-Lafayette, same months (Jan-Apr) compared",
            transform=ax.transAxes, ha="center", va="top", fontsize=11, style="italic", color="#555")
    footer(fig); fig.tight_layout(rect=[0,0.04,1,1])
    fig.savefig(OUT/"A3_is_2026_better.png"); plt.close(fig)


def _ranked():
    df = con.sql(f"SELECT * FROM read_parquet('{SCORE}', hive_partitioning=1)").df()
    r = df[df["meets_min_flights"]==True].sort_values("hotspot_score_base",ascending=False).reset_index(drop=True)
    return r


def chart_B1():
    r=_ranked(); N=len(r); k=int(round(N*0.05)); worst=r.head(k)
    ops=["PSA_operated","AA_mainline","Envoy_operated"]
    LAB={"PSA_operated":"American Eagle\n- PSA","AA_mainline":"American\n(mainline)","Envoy_operated":"American Eagle\n- Envoy"}
    flt=[r.loc[r.operator_class==o,"flights_total"].sum()/r["flights_total"].sum() for o in ops]
    wst=[(worst.operator_class==o).mean() for o in ops]
    import numpy as np
    x=np.arange(len(ops)); w=0.36
    fig, ax = plt.subplots(figsize=(13.5,6.8))
    b1=ax.bar(x-w/2, flt, w, label="Share of all flights", color=C_FLT)
    b2=ax.bar(x+w/2, wst, w, label="Share of the worst-performing routes", color=C_BAD)
    for bars in (b1,b2):
        for b in bars:
            ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.01, f"{b.get_height()*100:.0f}%", ha="center", fontsize=12, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([LAB[o] for o in ops])
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title("One operator flies 1 in 8 flights - but half the worst trouble spots", pad=16, fontsize=18)
    ax.legend(loc="upper right", frameon=False, fontsize=12)
    ax.set_ylim(0,0.62)
    ax.annotate("PSA: 4x over-represented", xy=(0+w/2,0.52), xytext=(0.4,0.58), fontsize=11, color=C_PSA,
                arrowprops=dict(arrowstyle="->",color=C_PSA))
    ax.annotate("Envoy: under-represented\n(the fairness check)", xy=(2+w/2,0.024), xytext=(1.45,0.30), fontsize=10.5, color=C_ENVOY,
                arrowprops=dict(arrowstyle="->",color=C_ENVOY))
    footer(fig); fig.tight_layout(rect=[0,0.04,1,1])
    fig.savefig(OUT/"B1_one_operator_half_the_trouble.png"); plt.close(fig)


def chart_B2():
    r=_ranked(); N=len(r); k=int(round(N*0.05)); worst=r.head(k)
    hubs=r.groupby("hub_family")["flights_total"].sum().sort_values(ascending=False)
    hubs=hubs[hubs.index!="focal_corridor"]
    order=list(hubs.index)
    flt=[hubs[h]/hubs.sum() for h in order]
    wst=[(worst.hub_family==h).mean() for h in order]
    import numpy as np
    x=np.arange(len(order)); w=0.4
    fig, ax = plt.subplots(figsize=(13,6.6))
    ax.bar(x-w/2, flt, w, label="Share of all flights", color=C_FLT)
    ax.bar(x+w/2, wst, w, label="Share of the worst-performing routes", color=C_BAD)
    ax.set_xticks(x); ax.set_xticklabels(order, fontsize=13)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title("Size doesn't predict trouble - the biggest hubs aren't the worst", pad=16)
    ax.legend(loc="upper right", frameon=False, fontsize=12)
    for h,xi,fv,wv in zip(order,x,flt,wst):
        if h in ("LAX","PHX","JFK"):
            ax.annotate("big, but clean", xy=(xi+w/2, wv+0.005), xytext=(xi, 0.18+0.0), fontsize=9.5, color=C_ENVOY, ha="center")
    footer(fig); fig.tight_layout(rect=[0,0.04,1,1])
    fig.savefig(OUT/"B2_size_doesnt_predict_trouble.png"); plt.close(fig)


if __name__ == "__main__":
    chart_A1(); chart_A2(); chart_A3(); chart_B1(); chart_B2()
    print("Rendered to", OUT)
    for p in sorted(OUT.glob("*.png")):
        print("  ", p.name, f"({p.stat().st_size//1024} KB)")
