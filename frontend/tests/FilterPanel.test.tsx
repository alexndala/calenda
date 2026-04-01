import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FilterPanel } from "@/components/FilterPanel";
import { useCalendaStore } from "@/lib/store";

// Mock TickerSearch since it uses API hooks
vi.mock("@/components/TickerSearch", () => ({
  TickerSearch: () => <div data-testid="ticker-search" />,
}));

describe("FilterPanel", () => {
  beforeEach(() => {
    useCalendaStore.setState({
      selectedTypes: new Set(["earnings", "dividend"]),
      universe: "sp500",
      customTickers: [],
      timingFilters: new Set(["BMO", "AMC", "TNS"]),
    });
  });

  it("renders event type checkboxes", () => {
    render(<FilterPanel />);
    expect(screen.getByLabelText("Earnings")).toBeInTheDocument();
    expect(screen.getByLabelText("Dividends")).toBeInTheDocument();
    expect(screen.getByLabelText("Splits")).toBeInTheDocument();
    expect(screen.getByLabelText("IPOs")).toBeInTheDocument();
  });

  it("unchecks split type on click", () => {
    render(<FilterPanel />);
    const splitsCheckbox = screen.getByLabelText("Splits");
    expect((splitsCheckbox as HTMLInputElement).checked).toBe(false);
    fireEvent.click(splitsCheckbox);
    expect(useCalendaStore.getState().selectedTypes.has("split")).toBe(true);
  });

  it("switches universe to NASDAQ 100", () => {
    render(<FilterPanel />);
    fireEvent.click(screen.getByText("NASDAQ 100"));
    expect(useCalendaStore.getState().universe).toBe("nasdaq100");
  });

  it("shows TickerSearch when Custom universe selected", () => {
    useCalendaStore.setState({ universe: "custom" });
    render(<FilterPanel />);
    expect(screen.getByTestId("ticker-search")).toBeInTheDocument();
  });

  it("does not show TickerSearch for sp500 universe", () => {
    render(<FilterPanel />);
    expect(screen.queryByTestId("ticker-search")).not.toBeInTheDocument();
  });
});
