import { CalendarDays, Check, ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
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
const MONTHS_SHORT = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

function toISO(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function parseYM(monthStr) {
  const [y, m] = monthStr.split("-").map(Number);
  return { year: y, month: m - 1 };
}

// currentMonth — 'YYYY-MM', задаёт начальный месяц
// onMonthChange — вызывается когда пользователь кликает по названию месяца
export function ScheduleDatePicker({
  selectedDates,
  onChange,
  currentMonth,
  onMonthChange,
  existingDates = [],
}) {
  const [isOpen, setIsOpen] = useState(false);

  const initNav = () => {
    if (selectedDates.length > 0) return parseYM(selectedDates[0].slice(0, 7));
    if (currentMonth) return parseYM(currentMonth);
    return { year: new Date().getFullYear(), month: new Date().getMonth() };
  };

  const [viewYear, setViewYear] = useState(() => initNav().year);
  const [viewMonth, setViewMonth] = useState(() => initNav().month);

  // lockedMonth — месяц, в котором разрешён выбор дат
  const [lockedMonth, setLockedMonth] = useState(() => {
    if (selectedDates.length > 0) return parseYM(selectedDates[0].slice(0, 7));
    if (currentMonth) return parseYM(currentMonth);
    return null;
  });

  const wrapperRef = useRef(null);

  useEffect(() => {
    function handler(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setIsOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Синхронизируем навигацию когда currentMonth меняется снаружи (без ручного выбора)
  useEffect(() => {
    if (selectedDates.length === 0 && currentMonth) {
      const { year, month } = parseYM(currentMonth);
      setViewYear(year);
      setViewMonth(month);
      setLockedMonth({ year, month });
    }
  }, [currentMonth, selectedDates.length]);

  useEffect(() => {
    if (selectedDates.length === 0 && !currentMonth) setLockedMonth(null);
  }, [selectedDates, currentMonth]);

  function navigate(delta) {
    const d = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(d.getFullYear());
    setViewMonth(d.getMonth());
  }

  // Клик по названию месяца — переключить весь месяц без выбора конкретных дат
  function handleSelectMonth() {
    const ym = `${viewYear}-${String(viewMonth + 1).padStart(2, "0")}`;
    setLockedMonth({ year: viewYear, month: viewMonth });
    onChange([]); // сбрасываем даты — расписание покажется за весь месяц
    onMonthChange?.(ym); // сообщаем родителю новый currentMonth
    setIsOpen(false);
  }

  function toggleDay(day) {
    const iso = toISO(viewYear, viewMonth, day);
    const isSelected = selectedDates.includes(iso);
    if (isSelected) {
      const next = selectedDates.filter((d) => d !== iso);
      onChange(next);
      if (next.length === 0) setLockedMonth(null);
    } else {
      if (!lockedMonth) setLockedMonth({ year: viewYear, month: viewMonth });
      onChange([...selectedDates, iso].sort());
    }
  }

  function clearAll() {
    onChange([]);
    setLockedMonth(null);
    onMonthChange?.(null);
  }

  function renderGrid() {
    const firstDay = new Date(viewYear, viewMonth, 1).getDay();
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const cells = [];
    for (let i = 0; i < firstDay; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    while (cells.length % 7 !== 0) cells.push(null);

    const monthLocked =
      lockedMonth && (lockedMonth.year !== viewYear || lockedMonth.month !== viewMonth);

    return cells.map((day, idx) => {
      if (!day) return <div key={`e-${idx}`} className="aspect-square" />;
      const iso = toISO(viewYear, viewMonth, day);
      const isSelected = selectedDates.includes(iso);
      const isDisabled = !!monthLocked;
      const isToday = iso === new Date().toISOString().slice(0, 10);
      const isExisting = existingDates.includes(iso);
      return (
        <button
          type="button"
          key={iso}
          onClick={() => !isDisabled && toggleDay(day)}
          disabled={isDisabled}
          className={[
            "aspect-square flex items-center justify-center text-[10px] font-bold transition-all rounded-lg relative",
            isDisabled
              ? "text-slate-200 cursor-not-allowed"
              : isSelected
                ? "bg-blue-600 text-white shadow-sm scale-105 cursor-pointer"
                : "text-slate-600 hover:bg-blue-50 hover:text-blue-600 cursor-pointer",
            isToday && !isSelected && !isDisabled ? "ring-1 ring-blue-300" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {day}
          {isExisting && !isSelected && (
            <span className="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-slate-400" />
          )}
          {isExisting && isSelected && (
            <span className="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-blue-200" />
          )}
        </button>
      );
    });
  }

  function getTriggerLabel() {
    if (lockedMonth) {
      const { year, month } = lockedMonth;
      const monthLabel = `${MONTHS_SHORT[month]} ${year}`;
      return selectedDates.length > 0 ? `${selectedDates.length} days · ${monthLabel}` : monthLabel;
    }
    return "Select period…";
  }

  const hasSelection = !!lockedMonth;
  const isCurrentMonthActive =
    lockedMonth && lockedMonth.year === viewYear && lockedMonth.month === viewMonth;

  return (
    <div className="relative" ref={wrapperRef}>
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className={[
          "flex justify-between items-center bg-slate-50 border px-3 py-2 text-[11px] rounded-2xl font-black transition-all hover:bg-slate-100 gap-3 cursor-pointer min-w-[160px]",
          isOpen
            ? "border-blue-400 bg-blue-50"
            : hasSelection
              ? "border-blue-200"
              : "border-slate-100",
        ].join(" ")}
      >
        <span className={hasSelection ? "text-blue-600" : "text-slate-500"}>
          {getTriggerLabel()}
        </span>
        <CalendarDays size={14} className={hasSelection ? "text-blue-500" : "text-slate-400"} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-[150] bg-white border border-slate-200 shadow-2xl rounded-2xl w-64 overflow-hidden">
          {lockedMonth && (
            <div className="px-4 pt-2.5 text-[9px] text-slate-400 font-bold flex items-center justify-center">
              Locked to {MONTHS_EN[lockedMonth.month]} {lockedMonth.year}
              <button
                type="button"
                onClick={clearAll}
                className="ml-2 text-blue-400 hover:text-blue-600 cursor-pointer"
              >
                reset
              </button>
            </div>
          )}

          {/* Nav — month name is a button */}
          <div className="flex items-center justify-between px-4 pt-3 pb-2">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="p-1 hover:bg-slate-50 rounded-lg text-slate-400 hover:text-blue-600 cursor-pointer transition-colors"
            >
              <ChevronLeft size={14} />
            </button>

            <button
              type="button"
              onClick={handleSelectMonth}
              title="Click to show whole month schedule"
              className={[
                "text-[11px] font-black uppercase tracking-tight px-2 py-1 rounded-lg transition-all cursor-pointer",
                isCurrentMonthActive && selectedDates.length === 0
                  ? "text-blue-600 bg-blue-50"
                  : "text-slate-600 hover:text-blue-600 hover:bg-blue-50",
              ].join(" ")}
            >
              {MONTHS_EN[viewMonth]} {viewYear}
            </button>

            <button
              type="button"
              onClick={() => navigate(1)}
              className="p-1 hover:bg-slate-50 rounded-lg text-slate-400 hover:text-blue-600 cursor-pointer transition-colors"
            >
              <ChevronRight size={14} />
            </button>
          </div>

          {/* Day grid */}
          <div className="px-3 pb-2">
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
            <div className="grid grid-cols-7 gap-0.5">{renderGrid()}</div>
          </div>

          {/* Footer */}
          <div className="border-t border-slate-100 px-3 py-2.5 flex items-center justify-between gap-2">
            <span
              className={`text-[10px] font-bold ${selectedDates.length > 0 ? "text-blue-600" : "text-slate-400"}`}
            >
              {selectedDates.length === 0
                ? lockedMonth
                  ? "Whole month · click dates to filter"
                  : "Click month name or dates"
                : `${selectedDates.length} date${selectedDates.length !== 1 ? "s" : ""} selected`}
            </span>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider bg-slate-900 text-white hover:bg-black shadow-sm cursor-pointer transition-all flex-shrink-0"
            >
              <Check size={11} /> Apply
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
