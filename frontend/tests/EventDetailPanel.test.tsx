import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { EventDetailPanel } from "@/components/EventDetailPanel";
import { useCalendaStore } from "@/lib/store";
import type { EarningsDetail } from "@/lib/types";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock useEventDetail hook
vi.mock("@/lib/api", () => ({
  useEventDetail: vi.fn(),
}));

import { useEventDetail } from "@/lib/api";

const mockDetail: EarningsDetail = {
  eps_estimate: 1.62,
  revenue_estimate: 94_000_000_000,
  analyst_count: null,
  beat_miss_history: [
    {
      quarter: "2025Q4",
      eps_actual: 1.6,
      eps_estimate: 1.5,
      eps_beat: true,
      rev_actual: 90e9,
      rev_estimate: 88e9,
      rev_beat: true,
    },
  ],
  eps_beat_rate: 0.875,
  rev_beat_rate: 0.75,
  price_reaction_by_day: [
    { day: -5, median_pct: -0.5, p25: -1.0, p75: 0.2 },
    { day: 0, median_pct: 2.3, p25: 0.5, p75: 4.1 },
    { day: 5, median_pct: 0.8, p25: -0.3, p75: 1.9 },
  ],
  eps_trend: [1.2, 1.3, 1.4, 1.5, 1.58, 1.6],
  insufficient_history: false,
};

function Wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient();
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("EventDetailPanel", () => {
  beforeEach(() => {
    useCalendaStore.setState({
      openEventId: "earnings-AAPL-2026-04-30",
      openEventTicker: "AAPL",
    });
    (useEventDetail as ReturnType<typeof vi.fn>).mockReturnValue({
      data: mockDetail,
      isLoading: false,
      isError: false,
    });
  });

  it("renders ticker name in header", () => {
    render(<Wrapper><EventDetailPanel /></Wrapper>);
    expect(screen.getByText("AAPL")).toBeInTheDocument();
  });

  it("renders EPS estimate", () => {
    render(<Wrapper><EventDetailPanel /></Wrapper>);
    expect(screen.getByText("$1.62")).toBeInTheDocument();
  });

  it("renders beat rates", () => {
    render(<Wrapper><EventDetailPanel /></Wrapper>);
    expect(screen.getByText("88%")).toBeInTheDocument(); // 0.875 → 88%
    expect(screen.getByText("75%")).toBeInTheDocument(); // 0.75 → 75%
  });

  it("closes on X button click", () => {
    render(<Wrapper><EventDetailPanel /></Wrapper>);
    fireEvent.click(screen.getByLabelText("Close panel"));
    expect(useCalendaStore.getState().openEventId).toBeNull();
  });

  it("closes on Escape key", () => {
    render(<Wrapper><EventDetailPanel /></Wrapper>);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(useCalendaStore.getState().openEventId).toBeNull();
  });

  it("shows skeleton when loading", () => {
    (useEventDetail as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });
    const { container } = render(<Wrapper><EventDetailPanel /></Wrapper>);
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });

  it("shows error state when API fails", () => {
    (useEventDetail as ReturnType<typeof vi.fn>).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });
    render(<Wrapper><EventDetailPanel /></Wrapper>);
    expect(screen.getByText(/No earnings analytics available/)).toBeInTheDocument();
  });
});
