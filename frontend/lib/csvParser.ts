/**
 * Broker CSV parser with auto-detection for common formats.
 * Supported: Schwab, Fidelity, IBKR, and generic (ticker, shares, avg_cost).
 */
import type { Position } from "./types";

export class UnrecognizedFormatError extends Error {
  constructor(public headers: string[]) {
    super("UNRECOGNIZED_FORMAT");
    this.name = "UnrecognizedFormatError";
  }
}

interface BrokerFormat {
  name: string;
  tickerCol: string;
  sharesCol: string;
  avgCostCol: string;
  /** If true, avgCostCol is total cost basis — divide by shares to get per-share cost */
  avgCostIsTotal?: boolean;
}

const BROKER_FORMATS: BrokerFormat[] = [
  {
    name: "Schwab",
    tickerCol: "Symbol",
    sharesCol: "Qty",
    avgCostCol: "Cost Basis",
    avgCostIsTotal: true,
  },
  {
    name: "Fidelity",
    tickerCol: "Symbol",
    sharesCol: "Quantity",
    avgCostCol: "Average Cost Basis",
  },
  {
    name: "IBKR",
    tickerCol: "Symbol",
    sharesCol: "Quantity",
    avgCostCol: "Avg Cost",
  },
  {
    name: "Generic",
    tickerCol: "ticker",
    sharesCol: "shares",
    avgCostCol: "avg_cost",
  },
];

/** Strip currency symbols, commas, whitespace from a numeric string. */
function cleanNumber(val: string): number {
  return parseFloat(val.replace(/[$,\s%]/g, "")) || 0;
}

/** Simple CSV line parser — handles double-quoted fields with embedded commas. */
function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
    } else if (ch === "," && !inQuotes) {
      result.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  result.push(current);
  return result;
}

/** Find the header row index and matching broker format. */
function detectFormat(
  lines: string[]
): { headerIdx: number; format: BrokerFormat; headers: string[] } | null {
  for (let i = 0; i < Math.min(25, lines.length); i++) {
    const cells = parseCsvLine(lines[i]).map((c) =>
      c.trim().replace(/^"|"$/g, "")
    );
    const rowLower = cells.map((c) => c.toLowerCase());

    for (const fmt of BROKER_FORMATS) {
      const hasTickerCol = rowLower.includes(fmt.tickerCol.toLowerCase());
      const hasSharesCol = rowLower.includes(fmt.sharesCol.toLowerCase());
      if (hasTickerCol && hasSharesCol) {
        return { headerIdx: i, format: fmt, headers: cells };
      }
    }
  }
  return null;
}

/** True if the string looks like a valid equity ticker. */
function looksLikeTicker(val: string): boolean {
  return /^[A-Z]{1,6}(\.[A-Z]{1,2})?$/.test(val.toUpperCase());
}

export interface ParseResult {
  positions: Position[];
  detectedFormat: string;
  previewRows: string[][];
}

/**
 * Parse a broker CSV string into positions.
 * Throws UnrecognizedFormatError if no known format is detected.
 */
export function parseCsvPositions(csvText: string): ParseResult {
  const lines = csvText
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);

  const detected = detectFormat(lines);
  if (!detected) {
    // Return first few rows as headers hint for manual mapping UI
    const sampleHeaders = parseCsvLine(lines[0] ?? "").map((c) =>
      c.trim().replace(/^"|"$/g, "")
    );
    throw new UnrecognizedFormatError(sampleHeaders);
  }

  const { headerIdx, format, headers } = detected;

  const colIdx = (name: string) =>
    headers.findIndex((h) => h.toLowerCase() === name.toLowerCase());

  const tickerIdx = colIdx(format.tickerCol);
  const sharesIdx = colIdx(format.sharesCol);
  const avgCostIdx = colIdx(format.avgCostCol);

  const positions: Position[] = [];
  const previewRows: string[][] = [];

  for (let i = headerIdx + 1; i < lines.length; i++) {
    const cells = parseCsvLine(lines[i]).map((c) =>
      c.trim().replace(/^"|"$/g, "")
    );

    const rawTicker = cells[tickerIdx]?.toUpperCase() ?? "";
    if (!looksLikeTicker(rawTicker)) continue;

    const shares = cleanNumber(cells[sharesIdx] ?? "0");
    if (shares <= 0) continue; // skip zero/negative/short positions

    let avg_cost = avgCostIdx >= 0 ? cleanNumber(cells[avgCostIdx] ?? "0") : 0;
    if (format.avgCostIsTotal && shares > 0) {
      avg_cost = avg_cost / shares;
    }

    positions.push({ ticker: rawTicker, shares, avg_cost });

    if (previewRows.length < 5) {
      previewRows.push([rawTicker, String(shares), avg_cost.toFixed(2)]);
    }
  }

  return {
    positions,
    detectedFormat: format.name,
    previewRows,
  };
}
