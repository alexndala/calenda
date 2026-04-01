"use client";
import { useRef, useState } from "react";
import {
  parseCsvPositions,
  UnrecognizedFormatError,
} from "@/lib/csvParser";
import type { Position } from "@/lib/types";

interface Props {
  onImport: (positions: Position[]) => void;
}

interface Preview {
  format: string;
  rows: string[][];
  positions: Position[];
}

export function CsvUpload({ onImport }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  function processFile(file: File) {
    setError(null);
    setPreview(null);
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = (e.target?.result as string) ?? "";
      try {
        const result = parseCsvPositions(text);
        if (result.positions.length === 0) {
          setError("No valid positions found in file. Check that the file has ticker symbols and share quantities.");
          return;
        }
        setPreview({
          format: result.detectedFormat,
          rows: result.previewRows,
          positions: result.positions,
        });
      } catch (err) {
        if (err instanceof UnrecognizedFormatError) {
          setError(
            `Could not detect broker format. Use a CSV with columns: ticker, shares, avg_cost. ` +
            `Detected headers: ${err.headers.slice(0, 6).join(", ")}`
          );
        } else {
          setError("Failed to parse CSV. Make sure it is a valid CSV file.");
        }
      }
    };
    reader.readAsText(file);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }

  function handleConfirm() {
    if (preview) {
      onImport(preview.positions);
      setPreview(null);
    }
  }

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          dragging
            ? "border-slate-600 bg-slate-50"
            : "border-slate-300 hover:border-slate-400 hover:bg-slate-50"
        }`}
      >
        <p className="text-sm font-medium text-slate-700">
          Drop broker CSV here or click to browse
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Schwab, Fidelity, IBKR, or generic (ticker, shares, avg_cost)
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.txt"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 p-3 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Preview + confirm */}
      {preview && (
        <div className="rounded-md border border-slate-200 overflow-hidden">
          <div className="px-3 py-2 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <span className="text-xs font-medium text-slate-600">
              Detected: {preview.format} &middot; {preview.positions.length} positions
            </span>
            <span className="text-xs text-slate-400">Preview (first 5)</span>
          </div>
          <table className="w-full text-xs">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-1.5 text-left text-slate-500 font-medium">Ticker</th>
                <th className="px-3 py-1.5 text-right text-slate-500 font-medium">Shares</th>
                <th className="px-3 py-1.5 text-right text-slate-500 font-medium">Avg Cost</th>
              </tr>
            </thead>
            <tbody>
              {preview.rows.map((row, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="px-3 py-1.5 font-mono text-slate-800">{row[0]}</td>
                  <td className="px-3 py-1.5 text-right text-slate-700">{row[1]}</td>
                  <td className="px-3 py-1.5 text-right text-slate-700">
                    {parseFloat(row[2]) > 0 ? `$${row[2]}` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-3 py-2 bg-white border-t border-slate-200 flex gap-2">
            <button
              onClick={handleConfirm}
              className="px-3 py-1.5 bg-slate-900 text-white text-xs font-medium rounded hover:bg-slate-700 transition-colors"
            >
              Import {preview.positions.length} positions
            </button>
            <button
              onClick={() => setPreview(null)}
              className="px-3 py-1.5 text-slate-600 text-xs hover:text-slate-900 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-400">
          Positions are stored in your browser. Re-upload your CSV if you clear browser data.
        </p>
        <a
          href="/sample-portfolio.csv"
          download="sample-portfolio.csv"
          className="text-xs text-slate-500 hover:text-slate-900 underline underline-offset-2 whitespace-nowrap"
        >
          See sample CSV
        </a>
      </div>
    </div>
  );
}
