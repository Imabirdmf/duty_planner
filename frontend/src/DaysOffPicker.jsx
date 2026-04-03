import { CalendarDays, Check, ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];

const MONTHS_EN = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

function isSameDay(a, b) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function toISO(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function getDaysInMonth(year, month) {
  // month: 0-based
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  // Monday-based offset (0=Mon .. 6=Sun)
  let offset = firstDay.getDay() - 1;
  if (offset < 0) offset = 6;
  return { days: lastDay.getDate(), offset };
}

// ── Один календарь ──────────────────────────────────────────────
function CalendarGrid({
  year,
  month,
  mode,
  multiDates,
  rangeStart,
  rangeEnd,
  hoverDate,
  onDayClick,
  onDayHover,
  existingDates = [],
}) {
  const { days, offset } = getDaysInMonth(year, month);
  const cells = [];

  // Empty cells before month start
  for (let i = 0; i < offset; i++) cells.push(null);
  for (let d = 1; d <= days; d++) cells.push(new Date(year, month, d));

  // Fill to complete last row
  while (cells.length % 7 !== 0) cells.push(null);

  function classify(date) {
    if (!date) return "";
    const classes = [];

    if (mode === "multi") {
      const isSelected = multiDates.some((d) => isSameDay(d, date));
      if (isSelected) classes.push("selected");
    } else {
      const isStart = rangeStart && isSameDay(date, rangeStart);
      const isEnd = rangeEnd && isSameDay(date, rangeEnd);

      if (isStart) classes.push("range-start");
      if (isEnd) classes.push("range-end");

      if (rangeStart && !rangeEnd && hoverDate) {
        const lo = rangeStart < hoverDate ? rangeStart : hoverDate;
        const hi = rangeStart < hoverDate ? hoverDate : rangeStart;
        if (date > lo && date < hi) classes.push("in-range");
        if (isSameDay(date, hoverDate) && !isSameDay(date, rangeStart))
          classes.push("range-hover-end");
      } else if (rangeStart && rangeEnd) {
        const lo = rangeStart < rangeEnd ? rangeStart : rangeEnd;
        const hi = rangeStart < rangeEnd ? rangeEnd : rangeStart;
        if (date > lo && date < hi) classes.push("in-range");
      }
    }

    return classes.join(" ");
  }

  return (
    <div>
      {/* Weekday headers */}
      <div className="grid grid-cols-7 gap-0.5 mb-1">
        {WEEKDAYS.map((d) => (
          <div
            key={d}
            className="aspect-square flex items-center justify-center text-[9px] font-black text-slate-400"
          >
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7 gap-0.5">
        {cells.map((date, idx) => {
          if (!date) return <div key={`e-${idx}`} className="aspect-square" />;

          const cls = classify(date);
          const isRangeStart = cls.includes("range-start");
          const isRangeEnd = cls.includes("range-end") || cls.includes("range-hover-end");
          const isInRange = cls.includes("in-range");
          const isSelected = cls.includes("selected");
          const isToday = isSameDay(date, new Date());
          const isExisting = existingDates.includes(toISO(date));

          return (
            <button
              type="button"
              key={toISO(date)}
              onClick={() => onDayClick(date)}
              onMouseEnter={() => onDayHover?.(date)}
              className={[
                "aspect-square flex items-center justify-center text-[10px] font-bold transition-all rounded-lg relative",
                isRangeStart || isRangeEnd
                  ? "bg-blue-600 text-white shadow-sm"
                  : isSelected
                    ? "bg-blue-600 text-white shadow-sm scale-105"
                    : isInRange
                      ? "bg-blue-50 text-blue-700 rounded-none"
                      : "text-slate-600 hover:bg-blue-50 hover:text-blue-600",
                isToday && !isRangeStart && !isRangeEnd && !isSelected
                  ? "ring-1 ring-blue-300"
                  : "",
                isRangeStart && rangeEnd ? "rounded-r-none" : "",
                isRangeEnd && rangeStart ? "rounded-l-none" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {date.getDate()}
              {/* Dot indicator for existing days off */}
              {isExisting && !isSelected && !isRangeStart && !isRangeEnd && (
                <span className="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-slate-400" />
              )}
              {isExisting && (isSelected || isRangeStart || isRangeEnd) && (
                <span className="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-blue-200" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── Основной компонент ───────────────────────────────────────────
export function DaysOffPicker({ userId, onSuccess, api, onError, existingDates = [], vacationMonth }) {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState("multi"); // 'multi' | 'range'

  // Calendar navigation
  const [viewYear, setViewYear] = useState(new Date().getFullYear());
  const [viewMonth, setViewMonth] = useState(new Date().getMonth()); // 0-based

  // Multi-select state
  const [multiDates, setMultiDates] = useState([]);

  // Range state
  const [rangeStart, setRangeStart] = useState(null);
  const [rangeEnd, setRangeEnd] = useState(null);
  const [hoverDate, setHoverDate] = useState(null);

  // Request state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [_submitError, setSubmitError] = useState(null);

  const wrapperRef = useRef(null);

  useEffect(() => {
    if (isOpen && vacationMonth) {
      const [year, month] = vacationMonth.split("-").map(Number);
      setViewYear(year);
      setViewMonth(month - 1); // month 0-based
    }
  }, [isOpen, vacationMonth]);

  // Close on outside click
  useEffect(() => {
    function handler(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  function navigateMonth(delta) {
    const d = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(d.getFullYear());
    setViewMonth(d.getMonth());
  }

  function handleModeSwitch(newMode) {
    setMode(newMode);
    setMultiDates([]);
    setRangeStart(null);
    setRangeEnd(null);
    setHoverDate(null);
    setSubmitError(null);
  }

  function handleDayClick(date) {
    setSubmitError(null);
    if (mode === "multi") {
      setMultiDates((prev) =>
        prev.some((d) => isSameDay(d, date))
          ? prev.filter((d) => !isSameDay(d, date))
          : [...prev, date]
      );
    } else {
      if (!rangeStart || (rangeStart && rangeEnd)) {
        setRangeStart(date);
        setRangeEnd(null);
        setHoverDate(null);
      } else {
        if (isSameDay(date, rangeStart)) {
          setRangeStart(null);
        } else if (date < rangeStart) {
          setRangeEnd(rangeStart);
          setRangeStart(date);
        } else {
          setRangeEnd(date);
        }
        setHoverDate(null);
      }
    }
  }

  // Build the list of dates to submit
  function getSelectedDates() {
    if (mode === "multi") {
      return [...multiDates].sort((a, b) => a - b).map(toISO);
    } else {
      if (!rangeStart || !rangeEnd) return [];
      const lo = rangeStart < rangeEnd ? rangeStart : rangeEnd;
      const hi = rangeStart < rangeEnd ? rangeEnd : rangeStart;
      const result = [];
      const cur = new Date(lo);
      while (cur <= hi) {
        result.push(toISO(cur));
        cur.setDate(cur.getDate() + 1);
      }
      return result;
    }
  }

  const selectedDates = getSelectedDates();
  const canApply = selectedDates.length > 0;

  async function handleApply() {
    if (!canApply || isSubmitting) return;
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      await api.post("/days-off/", {
        user: userId,
        dates: selectedDates,
      });

      // Reset & close
      setMultiDates([]);
      setRangeStart(null);
      setRangeEnd(null);
      setIsOpen(false);
      onSuccess?.();
    } catch (err) {
      const data = err.response?.data;
      let message = "Не удалось сохранить";
      if (data?.non_field_errors?.length) {
        message = data.non_field_errors[0];
      } else if (data?.dates) {
        const firstKey = Object.keys(data.dates)[0];
        const firstError = data.dates[firstKey];
        message = Array.isArray(firstError) ? firstError[0] : firstError;
      } else if (data?.detail) {
        message = data.detail;
      } else if (data?.error) {
        message = data.error;
      }
      onError?.(message);
      setMultiDates([]);
      setRangeStart(null);
      setRangeEnd(null);
    } finally {
      setIsSubmitting(false);
    }
  }

  // Trigger label
  function _getTriggerLabel() {
    if (selectedDates.length === 0) return null;
    if (mode === "range" && rangeStart && rangeEnd) {
      return `${rangeStart.getDate()} ${MONTHS_EN[rangeStart.getMonth()].slice(0, 3)} – ${rangeEnd.getDate()} ${MONTHS_EN[rangeEnd.getMonth()].slice(0, 3)}`;
    }
    if (mode === "multi") {
      return selectedDates.length === 1
        ? `${multiDates[0].getDate()} ${MONTHS_EN[multiDates[0].getMonth()].slice(0, 3)}`
        : `${selectedDates.length} days selected`;
    }
    return null;
  }

  const hasSelection = selectedDates.length > 0;

  return (
    <div className="relative" ref={wrapperRef}>
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className={[
          "p-1.5 border rounded-lg transition-all",
          isOpen
            ? "bg-blue-600 text-white border-blue-600 shadow-lg"
            : hasSelection
              ? "bg-blue-50 text-blue-600 border-blue-200 hover:border-blue-300"
              : "border-dashed border-slate-200 text-slate-400 hover:border-blue-300",
        ].join(" ")}
      >
        <CalendarDays size={14} />
      </button>

      {/* ── Dropdown popover ── */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 z-[200] bg-white border border-slate-200 shadow-2xl rounded-2xl w-72 animate-in zoom-in-95 overflow-hidden">
          {/* Mode tabs */}
          <div className="grid grid-cols-2 border-b border-slate-100">
            {["multi", "range"].map((m) => (
              <button
                type="button"
                key={m}
                onClick={() => handleModeSwitch(m)}
                className={[
                  "py-2.5 text-[10px] font-black uppercase tracking-widest transition-all",
                  mode === m
                    ? "text-blue-600 border-b-2 border-blue-600 -mb-px bg-blue-50/50"
                    : "text-slate-400 hover:text-slate-600",
                ].join(" ")}
              >
                {m === "multi" ? "◈ Multi-select" : "⟷ Range"}
              </button>
            ))}
          </div>

          {/* Calendar header */}
          <div className="flex items-center justify-between px-4 pt-3 pb-2">
            <button
              type="button"
              onClick={() => navigateMonth(-1)}
              className="p-1 hover:bg-slate-50 rounded-lg text-slate-400 hover:text-blue-600 transition-colors"
            >
              <ChevronLeft size={14} />
            </button>
            <span className="text-[11px] font-black uppercase text-slate-600 tracking-tight">
              {MONTHS_EN[viewMonth]} {viewYear}
            </span>
            <button
              onClick={() => navigateMonth(1)}
              className="p-1 hover:bg-slate-50 rounded-lg text-slate-400 hover:text-blue-600 transition-colors"
            >
              <ChevronRight size={14} />
            </button>
          </div>

          {/* Calendar grid */}
          <div className="px-3 pb-2" onMouseLeave={() => setHoverDate(null)}>
            <CalendarGrid
              year={viewYear}
              month={viewMonth}
              mode={mode}
              multiDates={multiDates}
              rangeStart={rangeStart}
              rangeEnd={rangeEnd}
              hoverDate={hoverDate}
              onDayClick={handleDayClick}
              onDayHover={mode === "range" ? setHoverDate : undefined}
              existingDates={existingDates}
            />
          </div>

          {/* Status + Apply */}
          <div className="border-t border-slate-100 px-3 py-2.5 flex items-center justify-between gap-2">
            <div className="text-[10px] text-slate-400 font-bold flex-1 min-w-0 truncate">
              {mode === "range" && !rangeStart && "Select start date"}
              {mode === "range" && rangeStart && !rangeEnd && (
                <span className="text-blue-500">
                  {rangeStart.getDate()} {MONTHS_EN[rangeStart.getMonth()].slice(0, 3)} → select end
                </span>
              )}
              {mode === "range" && rangeStart && rangeEnd && (
                <span className="text-blue-600">
                  {selectedDates.length} day{selectedDates.length !== 1 ? "s" : ""}
                </span>
              )}
              {mode === "multi" && multiDates.length === 0 && "Click dates to select"}
              {mode === "multi" && multiDates.length > 0 && (
                <span className="text-blue-600">
                  {multiDates.length} date{multiDates.length !== 1 ? "s" : ""} selected
                </span>
              )}
            </div>

            <button
              onClick={handleApply}
              disabled={!canApply || isSubmitting}
              className={[
                "flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex-shrink-0",
                canApply && !isSubmitting
                  ? "bg-slate-900 text-white hover:bg-black shadow-sm"
                  : "bg-slate-100 text-slate-300 cursor-not-allowed",
              ].join(" ")}
            >
              {isSubmitting ? (
                <span className="animate-pulse">Saving...</span>
              ) : (
                <>
                  <Check size={11} /> Apply
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
