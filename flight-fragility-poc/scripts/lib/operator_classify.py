"""scripts/lib/operator_classify.py — operator-class derivation for Fragility IV/V.

See flight_fragility_iv_operator_attribution_spec.md, "Operator-class
mapping" for the full methodology and source citations.

BTS On-Time Performance data has no marketing-carrier field distinct from
Reporting_Airline, so operator class is derived from carrier_code alone,
with two carriers (OO/SkyWest, YX/Republic) flagged as genuinely ambiguous
because each operates simultaneously under multiple mainline brands.
"""

from pathlib import Path

import pandas as pd
import yaml

# Routes already validated as AA-Eagle/UA-Express/DL-Connection markets in
# earlier Fragility studies — route_context_inference uses this mapping to
# resolve the ambiguous carriers' contract for flights on these specific
# routes only. It must not be extrapolated to markets outside this list.
BASKET_CONTRACT_LABEL = {
    "aa_regional_basket": "AA_contract",
    "ua_peer_basket": "UA_contract",
    "dl_peer_basket": "DL_contract",
}


def load_operator_classes(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def classify_operator(
    df: pd.DataFrame,
    operator_config: dict,
    carrier_col: str = "carrier_code",
    route_basket_col: str | None = "market_bucket",
) -> pd.DataFrame:
    """Add an `operator_class` column derived from carrier_code.

    Resolution order:
    1. Unambiguous carrier_code_map entries (AA, MQ, OH) map directly.
    2. Ambiguous carriers (OO, YX) on a route already inside a pre-validated
       basket get a route-context-inferred label, e.g. "SkyWest (AA_contract)".
    3. Any remaining ambiguous-carrier row gets the configured
       unresolved_class_label, pending scripts/14_resolve_operator_ambiguity.py.
    4. Everything else gets default_class (non-AA carriers encountered while
       filtering hub-spoke data to a hub airport, e.g. other airlines'
       flights through the same hub).
    """
    df = df.copy()
    carrier_map = operator_config.get("carrier_code_map", {})
    ambiguous = operator_config.get("ambiguous_carrier_codes", {})
    default_class = operator_config.get("default_class", "Other_or_non_AA")

    code_to_class = {code: spec["class"] for code, spec in carrier_map.items()}
    df["operator_class"] = df[carrier_col].map(code_to_class)

    for code, spec in ambiguous.items():
        mask = df[carrier_col] == code
        if not mask.any():
            continue
        unresolved_label = spec.get("unresolved_class_label", f"{code}_unresolved")
        df.loc[mask, "operator_class"] = unresolved_label

        if route_basket_col and route_basket_col in df.columns:
            for basket, contract_label in BASKET_CONTRACT_LABEL.items():
                basket_mask = mask & (df[route_basket_col] == basket)
                if basket_mask.any():
                    df.loc[basket_mask, "operator_class"] = f"{code}_{contract_label}"

    df["operator_class"] = df["operator_class"].fillna(default_class)
    return df


def apply_resolution_overrides(df: pd.DataFrame, resolution_path: Path,
                                key_cols: list[str] | None = None) -> pd.DataFrame:
    """Merge in any resolved operator classes from
    scripts/14_resolve_operator_ambiguity.py's output, overriding the
    unresolved fallback label where a resolution exists.

    No-op (returns df unchanged) if the resolution file doesn't exist or is
    empty — this keeps the calling scripts safe to run before any
    FlightAware resolution pass has ever been executed.
    """
    resolution_path = Path(resolution_path)
    if not resolution_path.exists():
        return df

    resolved = pd.read_csv(resolution_path)
    if resolved.empty:
        return df

    key_cols = key_cols or ["flight_date", "carrier_code", "flight_number", "origin", "dest"]
    key_cols = [c for c in key_cols if c in df.columns and c in resolved.columns]
    if not key_cols:
        return df

    df = df.merge(
        resolved[key_cols + ["resolved_operator_class"]],
        on=key_cols,
        how="left",
    )
    has_resolution = df["resolved_operator_class"].notna()
    df.loc[has_resolution, "operator_class"] = df.loc[has_resolution, "resolved_operator_class"]
    df = df.drop(columns=["resolved_operator_class"])
    return df
