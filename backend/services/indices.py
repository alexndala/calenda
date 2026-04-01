"""
Index constituent fetching.

US indices: Wikipedia pd.read_html() with hardcoded fallback.
International indices: hardcoded lists (Wikipedia coverage is inconsistent for non-US).

yfinance exchange suffixes used:
  .JO  — Johannesburg Stock Exchange (JSE)
  .T   — Tokyo Stock Exchange (TSE)
  .L   — London Stock Exchange (LSE)
  .SS  — Shanghai Stock Exchange
  .SZ  — Shenzhen Stock Exchange
  .PA  — Euronext Paris
  .DE  — XETRA (Frankfurt)
  .AS  — Euronext Amsterdam
  .MI  — Borsa Italiana (Milan)
  .MC  — Bolsa de Madrid

Note: yfinance earnings/EPS data coverage for non-US stocks is substantially thinner
than for US stocks. Calendar dates usually work; beat/miss history often won't.
"""
from __future__ import annotations
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# US indices
# ---------------------------------------------------------------------------

SP500_FALLBACK = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "BRK-B", "LLY", "AVGO",
    "TSLA", "JPM", "WMT", "V", "UNH", "XOM", "MA", "ORCL", "COST", "HD",
    "PG", "NFLX", "JNJ", "ABBV", "BAC", "CRM", "AMD", "MRK", "CVX", "KO",
    "ADBE", "PEP", "TMO", "ACN", "LIN", "MCD", "CSCO", "ABT", "GE", "DHR",
    "TXN", "AXP", "NEE", "WFC", "IBM", "PM", "ISRG", "INTU", "AMGN", "CAT",
]

NASDAQ100_FALLBACK = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "AVGO", "COST",
    "NFLX", "TMUS", "AMD", "ADBE", "PEP", "CSCO", "QCOM", "INTU", "AMGN", "TXN",
    "HON", "ISRG", "AMAT", "BKNG", "ADP", "SBUX", "GILD", "VRTX", "MDLZ", "REGN",
    "MU", "PANW", "KLAC", "LRCX", "ADI", "SNPS", "CDNS", "MELI", "ASML", "CSGP",
    "ORLY", "MNST", "AZN", "MAR", "FTNT", "WDAY", "TEAM", "DXCM", "IDXX", "CEG",
]

# ---------------------------------------------------------------------------
# JSE Top 40 — Johannesburg Stock Exchange (.JO suffix)
# ---------------------------------------------------------------------------

JSE_TOP40_FALLBACK = [
    "NPN.JO",  # Naspers
    "PRX.JO",  # Prosus
    "BHP.JO",  # BHP Group
    "AGL.JO",  # Anglo American
    "SOL.JO",  # Sasol
    "SBK.JO",  # Standard Bank
    "FSR.JO",  # FirstRand
    "SLM.JO",  # Sanlam
    "DSY.JO",  # Discovery
    "MTN.JO",  # MTN Group
    "VOD.JO",  # Vodacom
    "CFR.JO",  # Richemont (Cie Financière Richemont)
    "ABG.JO",  # Absa Group
    "CPI.JO",  # Capitec Bank
    "AMS.JO",  # Anglo American Platinum
    "IMP.JO",  # Impala Platinum
    "ANG.JO",  # AngloGold Ashanti
    "GFI.JO",  # Gold Fields
    "HAR.JO",  # Harmony Gold
    "WHL.JO",  # Woolworths Holdings
    "SPP.JO",  # Shoprite Holdings
    "MRP.JO",  # Mr Price Group
    "TFG.JO",  # The Foschini Group
    "CLS.JO",  # Clicks Group
    "NED.JO",  # Nedbank Group
    "BTI.JO",  # British American Tobacco
    "REM.JO",  # Remgro
    "GRT.JO",  # Growthpoint Properties
    "RDF.JO",  # Redefine Properties
    "LHC.JO",  # Life Healthcare
    "TBS.JO",  # Tiger Brands
    "AVI.JO",  # AVI Limited
    "INL.JO",  # Investec Limited
    "OMU.JO",  # Old Mutual
    "BVT.JO",  # Bidvest Group
    "SNH.JO",  # Steinhoff International
    "MCG.JO",  # MultiChoice Group
    "PIK.JO",  # Pick n Pay Stores
    "EMI.JO",  # Emira Property Fund
    "VKE.JO",  # Vukile Property Fund
]

# ---------------------------------------------------------------------------
# JSE All Share (ALSI) — top ~100 constituents
# ---------------------------------------------------------------------------

JSE_ALLSHARE_FALLBACK = JSE_TOP40_FALLBACK + [
    "RNI.JO",  # Reinet Investments
    "OML.JO",  # Old Mutual (alternate listing)
    "SUI.JO",  # Sun International
    "ACL.JO",  # ArcelorMittal South Africa
    "RCL.JO",  # RCL Foods
    "BAT.JO",  # Brait
    "OCE.JO",  # Oceana Group
    "ARA.JO",  # Attacq
    "HCI.JO",  # Hosken Consolidated Investments
    "TRU.JO",  # Truworths International
    "WBO.JO",  # Wilson Bayly Holmes-Ovcon
    "NPK.JO",  # Nampak
    "ADH.JO",  # Adcock Ingram
    "DCP.JO",  # Dis-Chem Pharmacies
    "SSW.JO",  # Sibanye Stillwater
    "EXX.JO",  # Exxaro Resources
    "MEI.JO",  # Mediclinic International
    "FFB.JO",  # Fortress REIT B
    "SAP.JO",  # Sappi
    "TKG.JO",  # Telkom SA
    "BAW.JO",  # Barloworld
    "IPL.JO",  # Imperial Logistics
    "MML.JO",  # Mediclinic (alternate)
    "AEG.JO",  # Aeci
    "ATT.JO",  # Attacq (alternate)
    "PPH.JO",  # Pepkor Holdings
    "KST.JO",  # PSG Konsult
    "PSG.JO",  # PSG Group
    "EPP.JO",  # EPP NV
    "HMN.JO",  # Hammerson
    "PPC.JO",  # PPC Limited (cement)
    "CVH.JO",  # Curro Holdings
    "CCO.JO",  # Capital & Counties
    "SRE.JO",  # Sirius Real Estate
    "MSM.JO",  # Massmart Holdings
    "RBX.JO",  # Raubex Group
    "KAP.JO",  # KAP Industrial Holdings
    "APN.JO",  # Aspen Pharmacare
    "MDC.JO",  # Mediclinic
    "COM.JO",  # Comair
]

# ---------------------------------------------------------------------------
# TOPIX Core 30 — Tokyo Stock Exchange (.T suffix)
# TOPIX has 1,800+ stocks; Core 30 are the 30 most liquid/large by mkt cap.
# Using numeric tickers as used by TSE / yfinance.
# ---------------------------------------------------------------------------

TOPIX_FALLBACK = [
    "7203.T",   # Toyota Motor
    "6758.T",   # Sony Group
    "8306.T",   # Mitsubishi UFJ Financial
    "9984.T",   # SoftBank Group
    "6861.T",   # Keyence
    "4063.T",   # Shin-Etsu Chemical
    "7974.T",   # Nintendo
    "9432.T",   # NTT (Nippon Telegraph & Telephone)
    "8316.T",   # Sumitomo Mitsui Financial
    "4519.T",   # Chugai Pharmaceutical
    "6098.T",   # Recruit Holdings
    "8035.T",   # Tokyo Electron
    "9433.T",   # KDDI Corporation
    "7267.T",   # Honda Motor
    "6367.T",   # Daikin Industries
    "4661.T",   # Oriental Land (Tokyo Disneyland)
    "8766.T",   # Tokio Marine Holdings
    "9022.T",   # Central Japan Railway
    "4502.T",   # Takeda Pharmaceutical
    "6501.T",   # Hitachi
    "6702.T",   # Fujitsu
    "4568.T",   # Daiichi Sankyo
    "7751.T",   # Canon
    "6594.T",   # Nidec (Nikkei)
    "7741.T",   # HOYA Corporation
    "4543.T",   # Terumo Corporation
    "8591.T",   # ORIX Corporation
    "6971.T",   # Kyocera
    "9020.T",   # East Japan Railway
    "3382.T",   # Seven & i Holdings
]

# ---------------------------------------------------------------------------
# FTSE 100 — London Stock Exchange (.L suffix)
# ---------------------------------------------------------------------------

FTSE100_FALLBACK = [
    "SHEL.L",  # Shell
    "AZN.L",   # AstraZeneca
    "HSBA.L",  # HSBC Holdings
    "ULVR.L",  # Unilever
    "BP.L",    # BP
    "RIO.L",   # Rio Tinto
    "GSK.L",   # GSK (GlaxoSmithKline)
    "DGE.L",   # Diageo
    "REL.L",   # RELX
    "NG.L",    # National Grid
    "LSEG.L",  # London Stock Exchange Group
    "VOD.L",   # Vodafone
    "AAL.L",   # Anglo American
    "BAT.L",   # British American Tobacco
    "IMB.L",   # Imperial Brands
    "PRU.L",   # Prudential
    "LLOY.L",  # Lloyds Banking Group
    "BARC.L",  # Barclays
    "NWG.L",   # NatWest Group
    "STAN.L",  # Standard Chartered
    "RKT.L",   # Reckitt Benckiser
    "EXPN.L",  # Experian
    "AHT.L",   # Ashtead Group
    "CNA.L",   # Centrica
    "ABF.L",   # Associated British Foods
    "TSCO.L",  # Tesco
    "MKS.L",   # Marks & Spencer
    "SBRY.L",  # Sainsbury's
    "WPP.L",   # WPP
    "BRBY.L",  # Burberry
    "PSON.L",  # Pearson
    "SSE.L",   # SSE
    "SGE.L",   # Sage Group
    "AUTO.L",  # Auto Trader Group
    "LAND.L",  # Land Securities
    "BME.L",   # B&M European Value Retail
    "EZJ.L",   # easyJet
    "IHG.L",   # InterContinental Hotels
    "IAG.L",   # International Airlines Group
    "BA.L",    # BAE Systems
    "RR.L",    # Rolls-Royce
    "FERG.L",  # Ferguson
    "SKG.L",   # Smurfit Kappa
    "CCL.L",   # Carnival
    "CPG.L",   # Compass Group
    "ENT.L",   # Entain
    "BLND.L",  # British Land
    "BT-A.L",  # BT Group
    "MNG.L",   # M&G
    "INF.L",   # Informa
    "SPX.L",   # Spirax-Sarco
    "MNDI.L",  # Mondi
    "PSN.L",   # Persimmon
    "TW.L",    # Taylor Wimpey
    "BWY.L",   # Bellway
    "ANTO.L",  # Antofagasta
    "GLEN.L",  # Glencore
    "EVR.L",   # Evraz (suspended — kept for completeness)
    "SDR.L",   # Schroders
    "HLMA.L",  # Halma
    "IMI.L",   # IMI
    "SMDS.L",  # DS Smith
    "RS1.L",   # RS Group
    "SMIN.L",  # Smiths Group
    "SVT.L",   # Severn Trent
    "UU.L",    # United Utilities
    "PNN.L",   # Pennon Group
    "WTB.L",   # Whitbread
    "JD.L",    # JD Sports Fashion
    "OCDO.L",  # Ocado Group
    "DPLM.L",  # Diploma
    "RTO.L",   # Rentokil Initial
    "BDEV.L",  # Barratt Developments
    "MRO.L",   # Melrose Industries
    "WEIR.L",  # Weir Group
    "ICP.L",   # Intermediate Capital Group
    "HWDN.L",  # Howden Joinery
    "DCC.L",   # DCC
    "CRDA.L",  # Croda International
    "CSGP.L",  # CoStar Group
    "FRES.L",  # Fresnillo
    "POLYMETAL.L",  # Polymetal (suspended)
    "BNZL.L",  # Bunzl
    "GFS.L",   # G4S (now Aliaxis... check)
    "ITRK.L",  # Intertek Group
    "AV.L",    # Aviva
    "LGEN.L",  # Legal & General
    "PHX.L",   # Phoenix Group
    "JET2.L",  # Jet2
    "MNDI.L",  # Mondi
    "HTG.L",   # Hunting
    "CRH.L",   # CRH
    "KGF.L",   # Kingfisher
    "FLTR.L",  # Flutter Entertainment
    "III.L",   # 3i Group
    "HSX.L",   # Hiscox
    "BEZ.L",   # Beazley
    "ADN.L",   # Aberdeen
    "AST.L",   # Astracast... (check)
]

# ---------------------------------------------------------------------------
# FTSE China A50 — top 50 A-shares by market cap
# Shanghai (.SS) and Shenzhen (.SZ) exchange suffixes
# ---------------------------------------------------------------------------

FTSE_CHINA_A50_FALLBACK = [
    "600519.SS",  # Kweichow Moutai
    "601318.SS",  # Ping An Insurance
    "600036.SS",  # China Merchants Bank
    "600900.SS",  # Yangtze Power (China Yangtze)
    "601166.SS",  # Industrial Bank
    "601628.SS",  # China Life Insurance
    "601088.SS",  # China Shenhua Energy
    "600028.SS",  # Sinopec (China Petroleum & Chemical)
    "601857.SS",  # PetroChina
    "601398.SS",  # ICBC (Industrial & Commercial Bank of China)
    "601288.SS",  # Agricultural Bank of China
    "601939.SS",  # China Construction Bank
    "601988.SS",  # Bank of China
    "600030.SS",  # CITIC Securities
    "601012.SS",  # Longi Green Energy
    "300750.SZ",  # CATL (Contemporary Amperex Technology)
    "000858.SZ",  # Wuliangye Yibin
    "002594.SZ",  # BYD Company
    "000333.SZ",  # Midea Group
    "000651.SZ",  # Gree Electric Appliances
    "600887.SS",  # Inner Mongolia Yili Industrial
    "601601.SS",  # China Pacific Insurance
    "600016.SS",  # China Minsheng Banking
    "601328.SS",  # Bank of Communications
    "600000.SS",  # Shanghai Pudong Development Bank
    "601225.SS",  # Shaanxi Coal Industry
    "601669.SS",  # Power Construction Corp of China
    "601186.SS",  # China Railway Construction
    "601800.SS",  # China Communications Construction
    "601390.SS",  # China Railway Group
    "600050.SS",  # China United Network (China Unicom)
    "601111.SS",  # Air China
    "600115.SS",  # China Eastern Airlines
    "600029.SS",  # China Southern Airlines
    "601919.SS",  # COSCO Shipping Holdings
    "601211.SS",  # Guotai Junan Securities
    "600048.SS",  # Poly Developments and Holdings
    "600547.SS",  # Shandong Gold Mining
    "601899.SS",  # Zijin Mining Group
    "000002.SZ",  # Vanke (China Vanke)
    "002142.SZ",  # Bank of Ningbo
    "300059.SZ",  # East Money Information
    "002304.SZ",  # Jiangsu Yanghe Brewery
    "000568.SZ",  # Luzhou Laojiao
    "300015.SZ",  # Aier Eye Hospital Group
    "002352.SZ",  # S.F. Holding
    "300124.SZ",  # Shenzhen Inovance Technology
    "600690.SS",  # Haier Smart Home
    "601138.SS",  # Foxconn Industrial Internet
    "000播.SZ",   # placeholder — pad to 50
]

# Remove the placeholder and keep clean 49
FTSE_CHINA_A50_FALLBACK = [t for t in FTSE_CHINA_A50_FALLBACK if not t.startswith("000播")]

# ---------------------------------------------------------------------------
# EURO STOXX 50 — 50 largest Eurozone companies across multiple exchanges
# ---------------------------------------------------------------------------

EUROSTOXX50_FALLBACK = [
    # Netherlands (.AS)
    "ASML.AS",   # ASML Holding
    "INGA.AS",   # ING Group
    "PHIA.AS",   # Philips
    "PRX.AS",    # Prosus
    "AD.AS",     # Ahold Delhaize
    # France (.PA)
    "MC.PA",     # LVMH
    "TTE.PA",    # TotalEnergies
    "SAN.PA",    # Sanofi
    "AI.PA",     # Air Liquide
    "OR.PA",     # L'Oreal
    "AIR.PA",    # Airbus
    "BNP.PA",    # BNP Paribas
    "ACA.PA",    # Crédit Agricole
    "GLE.PA",    # Société Générale
    "SU.PA",     # Schneider Electric
    "DG.PA",     # Vinci
    "RI.PA",     # Pernod Ricard
    "KER.PA",    # Kering
    "CAP.PA",    # Capgemini
    "STM.PA",    # STMicroelectronics
    # Germany (.DE)
    "SAP.DE",    # SAP
    "SIE.DE",    # Siemens
    "ALV.DE",    # Allianz
    "MUV2.DE",   # Munich Re (Münchener Rück)
    "DTE.DE",    # Deutsche Telekom
    "BMW.DE",    # BMW
    "MBG.DE",    # Mercedes-Benz Group
    "BAYN.DE",   # Bayer
    "BASF.DE",   # BASF
    "DB1.DE",    # Deutsche Börse
    "ADS.DE",    # Adidas
    "IFX.DE",    # Infineon Technologies
    "RWE.DE",    # RWE
    "ENR.DE",    # Siemens Energy
    # Spain (.MC)
    "IBE.MC",    # Iberdrola
    "SAN.MC",    # Banco Santander
    "BBVA.MC",   # BBVA
    "ITX.MC",    # Inditex (Zara)
    # Italy (.MI)
    "ENEL.MI",   # Enel
    "ENI.MI",    # Eni
    "STLAM.MI",  # Stellantis
    "ISP.MI",    # Intesa Sanpaolo
    "UCG.MI",    # UniCredit
    "LDO.MI",    # Leonardo
    # Belgium (.BR)
    "ABI.BR",    # AB InBev (Anheuser-Busch InBev)
    # Finland (.HE)
    "NOKIA.HE",  # Nokia
    # Ireland (.IR)
    "CRH.IR",    # CRH
    # Luxembourg
    "SGEF.PA",   # Société Générale Equipment Finance (via Paris)
]

# ---------------------------------------------------------------------------
# Wikipedia sources (where reliable)
# ---------------------------------------------------------------------------

SP500_WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
NASDAQ100_WIKI_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"
FTSE100_WIKI_URL = "https://en.wikipedia.org/wiki/FTSE_100_index"
EUROSTOXX50_WIKI_URL = "https://en.wikipedia.org/wiki/EURO_STOXX_50"


def _normalize_ticker(sym: str) -> str:
    """Normalize BRK.B → BRK-B for US tickers (yfinance format)."""
    return sym.replace(".", "-").strip()


# ---------------------------------------------------------------------------
# Fetch functions
# ---------------------------------------------------------------------------

def get_sp500_tickers() -> list[str]:
    try:
        tables = pd.read_html(SP500_WIKI_URL)
        df = tables[0]
        if "Symbol" not in df.columns:
            raise ValueError("'Symbol' column not found")
        tickers = [_normalize_ticker(s) for s in df["Symbol"].tolist() if isinstance(s, str)]
        if len(tickers) < 400:
            raise ValueError(f"Only {len(tickers)} tickers — suspiciously low")
        logger.info("Loaded %d S&P 500 tickers from Wikipedia", len(tickers))
        return tickers
    except Exception as exc:
        logger.warning("S&P 500 Wikipedia fetch failed, using fallback: %s", exc)
        return SP500_FALLBACK


def get_nasdaq100_tickers() -> list[str]:
    try:
        tables = pd.read_html(NASDAQ100_WIKI_URL)
        for table in tables:
            cols = [c.lower() for c in table.columns]
            col_match = next(
                (table.columns[i] for i, c in enumerate(cols) if "ticker" in c or "symbol" in c),
                None,
            )
            if col_match:
                tickers = [_normalize_ticker(s) for s in table[col_match].tolist() if isinstance(s, str)]
                if len(tickers) >= 90:
                    logger.info("Loaded %d NASDAQ 100 tickers from Wikipedia", len(tickers))
                    return tickers
        raise ValueError("No suitable table found")
    except Exception as exc:
        logger.warning("NASDAQ 100 Wikipedia fetch failed, using fallback: %s", exc)
        return NASDAQ100_FALLBACK


def get_jse_top40_tickers() -> list[str]:
    """JSE Top 40 — hardcoded; no reliable Wikipedia source with .JO tickers."""
    return JSE_TOP40_FALLBACK


def get_jse_allshare_tickers() -> list[str]:
    """JSE All Share (ALSI) — top ~100 constituents, hardcoded."""
    return JSE_ALLSHARE_FALLBACK


def get_topix_tickers() -> list[str]:
    """
    TOPIX Core 30 — the 30 most liquid Tokyo Stock Exchange constituents.
    Full TOPIX has 1,800+ stocks; fetching all would exceed free API limits.
    """
    return TOPIX_FALLBACK


def get_ftse100_tickers() -> list[str]:
    """FTSE 100 — try Wikipedia (EPIC column + .L suffix), fall back to hardcoded."""
    try:
        tables = pd.read_html(FTSE100_WIKI_URL)
        for table in tables:
            cols = [str(c).lower() for c in table.columns]
            # Wikipedia FTSE 100 table has an "EPIC" or "Ticker" column
            col_match = next(
                (table.columns[i] for i, c in enumerate(cols) if c in ("epic", "ticker", "symbol")),
                None,
            )
            if col_match:
                tickers = [
                    f"{str(s).strip()}.L"
                    for s in table[col_match].tolist()
                    if isinstance(s, str) and s.strip() and not s.strip().startswith("(")
                ]
                if len(tickers) >= 80:
                    logger.info("Loaded %d FTSE 100 tickers from Wikipedia", len(tickers))
                    return tickers
        raise ValueError("No EPIC/Ticker column found")
    except Exception as exc:
        logger.warning("FTSE 100 Wikipedia fetch failed, using fallback: %s", exc)
        return FTSE100_FALLBACK


def get_ftse_china_a50_tickers() -> list[str]:
    """FTSE China A50 — hardcoded; no reliable Wikipedia source with numeric tickers."""
    return FTSE_CHINA_A50_FALLBACK


def get_eurostoxx50_tickers() -> list[str]:
    """EURO STOXX 50 — hardcoded; Wikipedia table doesn't contain yfinance tickers directly."""
    return EUROSTOXX50_FALLBACK
