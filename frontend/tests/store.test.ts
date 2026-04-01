import { describe, it, expect, beforeEach } from "vitest";
import { useCalendaStore } from "@/lib/store";

describe("CalendaStore", () => {
  beforeEach(() => {
    useCalendaStore.setState({
      viewMode: "calendar",
      selectedTypes: new Set(["earnings", "dividend"]),
      universe: "sp500",
      customTickers: [],
      timingFilters: new Set(["BMO", "AMC", "TNS"]),
      openEventId: null,
      openEventTicker: null,
    });
  });

  it("toggles event types", () => {
    const { toggleType } = useCalendaStore.getState();
    toggleType("split");
    expect(useCalendaStore.getState().selectedTypes.has("split")).toBe(true);
    toggleType("split");
    expect(useCalendaStore.getState().selectedTypes.has("split")).toBe(false);
  });

  it("opens and closes events", () => {
    const { openEvent, closeEvent } = useCalendaStore.getState();
    openEvent("earnings-AAPL-2026-04-30", "AAPL");
    expect(useCalendaStore.getState().openEventId).toBe("earnings-AAPL-2026-04-30");
    expect(useCalendaStore.getState().openEventTicker).toBe("AAPL");
    closeEvent();
    expect(useCalendaStore.getState().openEventId).toBeNull();
    expect(useCalendaStore.getState().openEventTicker).toBeNull();
  });

  it("switches universe", () => {
    const { setUniverse } = useCalendaStore.getState();
    setUniverse("nasdaq100");
    expect(useCalendaStore.getState().universe).toBe("nasdaq100");
  });

  it("default selected types are earnings and dividend", () => {
    const { selectedTypes } = useCalendaStore.getState();
    expect(selectedTypes.has("earnings")).toBe(true);
    expect(selectedTypes.has("dividend")).toBe(true);
    expect(selectedTypes.has("split")).toBe(false);
    expect(selectedTypes.has("ipo")).toBe(false);
  });

  it("date range change closes panel", () => {
    useCalendaStore.setState({ openEventId: "some-id", openEventTicker: "AAPL" });
    const { setDateRange } = useCalendaStore.getState();
    setDateRange(new Date("2026-05-01"), new Date("2026-05-31"));
    expect(useCalendaStore.getState().openEventId).toBeNull();
  });
});
