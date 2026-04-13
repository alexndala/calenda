"use client";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { EventClickArg, DatesSetArg } from "@fullcalendar/core";
import { useCalendarEvents } from "@/lib/api";
import { useCalendaStore } from "@/lib/store";
import type { CalendarEvent } from "@/lib/types";

function formatMarketCap(cap: number | null): string {
  if (cap === null) return "";
  if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`;
  if (cap >= 1e9) return `$${(cap / 1e9).toFixed(0)}B`;
  if (cap >= 1e6) return `$${(cap / 1e6).toFixed(0)}M`;
  return `$${cap}`;
}

export function CalendarView() {
  const { selectedTypes, universe, customTickers, timingFilters, openEvent, setDateRange } =
    useCalendaStore();

  const { currentDateRange } = useCalendaStore();
  const { start, end } = currentDateRange;

  const { data: events = [], isLoading, isError, refetch } = useCalendarEvents({
    start,
    end,
    index: universe,
    customTickers,
    types: Array.from(selectedTypes),
  });

  // Filter by timing (earnings only)
  const filtered = events.filter((e: CalendarEvent) => {
    if (e.type === "earnings" && e.timing) {
      return timingFilters.has(e.timing as "BMO" | "AMC" | "TNS");
    }
    return true;
  });

  const fcEvents = filtered.map((e: CalendarEvent) => ({
    id: e.id,
    title: e.ticker + (e.timing ? ` (${e.timing})` : ""),
    date: e.date,
    classNames: [`event-${e.type}`],
    extendedProps: {
      eventType: e.type,
      timing: e.timing,
      marketCap: e.market_cap,
      ticker: e.ticker,
      companyName: e.company_name,
      is_jse: e.ticker.endsWith('.JO'),
      calendarEvent: e,
    },
  }));

  function handleEventClick(arg: EventClickArg) {
    const { ticker, calendarEvent } = arg.event.extendedProps as { ticker: string; calendarEvent: CalendarEvent };
    openEvent(arg.event.id, ticker, calendarEvent);
  }

  function handleDatesSet(arg: DatesSetArg) {
    setDateRange(arg.start, arg.end);
  }

  return (
    <div className="h-full p-4 relative">
      {isLoading && (
        <div className="absolute inset-0 bg-white/70 z-10 flex items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-slate-500">Loading events...</span>
          </div>
        </div>
      )}
      {isError && (
        <div className="absolute inset-0 bg-white/90 z-10 flex items-center justify-center">
          <div className="text-center">
            <p className="text-sm text-red-600 mb-2">Failed to load events</p>
            <button
              onClick={() => refetch()}
              className="px-3 py-1 text-sm bg-slate-900 text-white rounded hover:bg-slate-700"
            >
              Retry
            </button>
          </div>
        </div>
      )}
      <FullCalendar
        plugins={[dayGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        events={fcEvents}
        eventClick={handleEventClick}
        datesSet={handleDatesSet}
        dayMaxEvents={4}
        moreLinkClick="popover"
        headerToolbar={{
          left: "prev,next today",
          center: "title",
          right: "",
        }}
        height="100%"
        eventClassNames={(arg) => [`event-${arg.event.extendedProps.eventType}`]}
        eventContent={(arg) => (
          <div className="flex items-center gap-0.5 truncate px-1">
            <span className="truncate">{arg.event.title}</span>
            {arg.event.extendedProps?.is_jse && (
              <span className="shrink-0 text-[9px] bg-green-100 text-green-700 px-0.5 rounded">SA</span>
            )}
          </div>
        )}
      />
    </div>
  );
}
