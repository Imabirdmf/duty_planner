import axios from "axios";
import {
  AlertCircle,
  BarChart2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Info,
  Play,
  RotateCcw,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { DaysOffPicker } from "./DaysOffPicker";
import { ScheduleDatePicker } from "./ScheduleDatePicker";

const API_URL = import.meta.env.PROD ? "" : import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { "Content-Type": "application/json" },
  timeout: 5000,
});

const MONTH_COLORS = [
  "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6",
  "#EF4444", "#06B6D4", "#F97316", "#84CC16",
  "#EC4899", "#6366F1", "#14B8A6", "#A855F7",
];

const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const toMonthLabel = (m) => MONTH_NAMES[(Number(m) - 1) % 12] ?? String(m);

// Формат ответа: { data: [{ user: id, duties: [{ month: int, duty_count: int }] }] }
const DutyAnalyticsTab = ({ users, api }) => {
  const [rows, setRows] = useState([]);
  const [months, setMonths] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hoveredRow, setHoveredRow] = useState(null);
  const [popoverPos, setPopoverPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const fetchStats = async (retryCount = 0) => {
      try {
        const now = new Date();
        const startDate = `${now.getFullYear()}-01-01`;
        const endDate = `${now.getFullYear()}-12-31`;
//         const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);
//         const endDate = endOfMonth.toISOString().slice(0, 10);

        const res = await api.get("/users/stats/", {
          params: { start_date: startDate, end_date: endDate },
        });
        const raw = res.data.data ?? res.data;

        const monthSet = new Set();
        raw.forEach(row => row.duties.forEach(d => monthSet.add(d.month)));
        const sortedMonths = Array.from(monthSet).sort((a, b) => a - b);
        setMonths(sortedMonths);

        const formatted = raw.map(row => {
          const user = users.find(u => u.id === row.user);
          return {
            userId: row.user,
            name: user ? (user.full_name || user.name) : `#${row.user}`,
            email: user?.email ?? "",
            duties: row.duties,
          };
        });
        setRows(formatted);
        setLoading(false);
      } catch (err) {
        if (retryCount < 4) {
          setTimeout(() => fetchStats(retryCount + 1), Math.pow(2, retryCount) * 1000);
        } else {
          setError("Error loading");
          setLoading(false);
        }
      }
    };
    fetchStats();
  }, [users]);

  if (loading)
    return (
      <div className="overflow-visible px-2 pb-2">
        <table className="w-full text-left table-fixed border-separate border-spacing-y-1">
          <thead>
            <tr className="text-[10px] uppercase font-black text-slate-400">
              <th className="px-6 py-3 w-0 whitespace-nowrap">Employee</th>
              <th className="px-3 py-3 w-full">Duties</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: users.length || 5 }).map((_, idx) => (
              <tr key={`skeleton-${idx}`} className="group">
                <td className="px-6 py-3 bg-slate-50/30 rounded-l-2xl transition-colors">
                  <div className="space-y-2">
                    <div className="h-4 bg-slate-200 rounded-lg w-24 animate-pulse" />
                    <div className="h-3 bg-slate-100 rounded-lg w-32 animate-pulse" />
                  </div>
                </td>
                <td className="px-6 py-3 bg-slate-50/30 rounded-r-2xl transition-colors">
                  <div className="flex flex-wrap gap-0.5">
                    {Array.from({ length: 8 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-3 h-7 rounded-lg bg-slate-200 animate-pulse flex-shrink-0"
                      />
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
  );
  if (error) return (
    <div className="py-20 text-center text-red-500 font-bold text-[10px] uppercase">{error}</div>
  );
  if (!rows.length) return (
    <div className="py-20 text-center text-slate-300 font-bold text-sm">Нет данных</div>
  );

    return (
    <div className="overflow-visible px-2 pb-2 relative">
        {/*Legend */}
      {months.length > 0 && !loading && (
        <div className="absolute top-0 right-16 bg-white">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] font-bold text-slate-600">
            {months.map(month => (
              <div key={month} className="flex items-center gap-1.5 whitespace-nowrap">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: MONTH_COLORS[months.indexOf(month) % MONTH_COLORS.length] }}
                />
                {toMonthLabel(month)}
              </div>
            ))}
          </div>
        </div>
      )}

      <table className="w-full text-left border-separate border-spacing-y-1">
        <thead>
          <tr className="text-[10px] uppercase font-black text-slate-400">
            <th className="px-6 py-3 w-0 whitespace-nowrap">Employee</th>
            <th className="px-3 py-3 w-full">Duties</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr
              key={row.userId}
              className="group"
              onMouseEnter={(e) => {
                setHoveredRow(row.userId);
                setPopoverPos({ x: e.clientX, y: e.clientY });
              }}
              onMouseLeave={() => setHoveredRow(null)}
            >
              <td className="px-6 py-3 whitespace-nowrap bg-slate-50/30 group-hover:bg-slate-50 rounded-l-2xl transition-colors align-middle">
                <div className="font-bold text-slate-800 text-sm truncate">{row.name}</div>
                <div className="text-[11px] text-slate-400 truncate mt-0.5">{row.email}</div>
              </td>
              <td className="px-3 py-3 bg-slate-50/30 group-hover:bg-slate-50 rounded-r-2xl transition-colors align-middle">
                <div className="flex flex-wrap gap-0.5">
                  {months.map(month => {
                    const duty = row.duties.find(d => d.month === month);
                    const count = duty?.duty_count ?? 0;
                    return Array.from({ length: count }).map((_, i) => {
                      const dutyId = `${row.userId}-${month}-${i}`;
                      return (
                        <div
                          key={dutyId}
                          style={{ backgroundColor: MONTH_COLORS[months.indexOf(month) % MONTH_COLORS.length] }}
                          className="w-3 h-7 rounded-lg flex-shrink-0"
                        />
                      );
                    });
                  })}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* ✅ Popover */}
      {hoveredRow && (
        <div
          style={{
            position: 'fixed',
            left: `${popoverPos.x}px`,
            top: `${popoverPos.y - 20}px`,
            transform: 'translate(-50%, -100%)',
          }}
          className="z-[1000] bg-white border border-slate-200 shadow-2xl rounded-2xl p-4 w-64 animate-in zoom-in-95"
        >
          {rows.find(r => r.userId === hoveredRow) && (() => {
            const row = rows.find(r => r.userId === hoveredRow);
            return (
              <>
                {/* Name */}
                <div className="font-bold text-slate-800 mb-3 pb-3 border-b border-slate-100">
                  {row.name}
                </div>

                {/* Month */}
                <div className="space-y-2 mb-3">
                  {row.duties.map(d => (
                    <div key={d.month} className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: MONTH_COLORS[months.indexOf(d.month) % MONTH_COLORS.length] }}
                      />
                      <span className="text-[11px] text-slate-600 flex-1">{toMonthLabel(d.month)}:</span>
                      <span className="text-[11px] font-bold text-slate-800">{d.duty_count}</span>
                    </div>
                  ))}
                </div>

                {/* Total */}
                <div className="border-t border-slate-100 pt-2 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400 font-bold">TOTAL</span>
                  <span className="text-[12px] font-black text-blue-600">
                    {row.duties.reduce((sum, d) => sum + d.duty_count, 0)}
                  </span>
                </div>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};

const App = () => {
  // currentMonth — стейт, задаёт какой месяц показывать в расписании
  const [currentMonth, setCurrentMonth] = useState(new Date().toISOString().slice(0, 7));
  const [vacationMonth, setVacationMonth] = useState(new Date().toISOString().slice(0, 7));
  const [staffTab, setStaffTab] = useState("staff"); // "staff" | "analytics"

  const [shiftSize, setShiftSize] = useState(2);
  const [users, setUsers] = useState([]);
  const [vacations, setVacations] = useState([]);
  const [selectedDutyDays, setSelectedDutyDays] = useState([]);
  const [timetable, setTimetable] = useState({});
  const [isDistributing, setIsDistributing] = useState(false);
  const [error, setError] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [highlightedDates, setHighlightedDates] = useState(new Set());

  const [activeEditPopover, setActiveEditPopover] = useState(null);
  const [activeAddUserPopover, setActiveAddUserPopover] = useState(null);

  const editRef = useRef(null);
  const addUserRef = useRef(null);

  const currentMonthLabel = new Date(`${currentMonth}-01`).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  // --- Helpers ---
  const getMonthRange = (monthStr) => {
    const [year, month] = monthStr.split("-").map(Number);
    const startDate = `${monthStr}-01`;
    const lastDay = new Date(year, month, 0).getDate();
    const endDate = `${monthStr}-${lastDay.toString().padStart(2, "0")}`;
    return { startDate, endDate };
  };

  const shiftMonth = (current, offset) => {
    const [year, month] = current.split("-").map(Number);
    const d = new Date(year, month - 1 + offset, 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  };

  // --- API ---
  const fetchUsers = useCallback(async () => {
    try {
      const res = await api.get("/users/");
      setUsers(res.data);
    } catch {
      setError("Failed to load users");
    }
  }, []);

  const fetchVacations = useCallback(async () => {
    const { startDate, endDate } = getMonthRange(vacationMonth);
    try {
      const res = await api.get("/days-off/", {
        params: { start_date: startDate, end_date: endDate },
      });
      setVacations(res.data);
      } catch {
      setError("Failed to load vacations");
      }
    }, [vacationMonth]);

  const fetchTimetable = useCallback(async () => {
    const { startDate, endDate } = getMonthRange(currentMonth);
    try {
      const res = await api.get("/duties/list_assignments/", {
        params: { start_date: startDate, end_date: endDate },
      });
      const items = res.data?.data || res.data;
      if (Array.isArray(items)) {
        const mapped = items.reduce((acc, item) => {
          acc[item.date] = item.users.map((u) => ({ id: u.id, name: u.full_name || u.name }));
          return acc;
        }, {});
        setTimetable(mapped);
      }
    } catch {
      setTimetable({});
    }
  }, [currentMonth]);

  useEffect(() => {
    fetchUsers();
  }, []);
  useEffect(() => {
    if (users.length > 0 && shiftSize > users.length) setShiftSize(users.length);
  }, [users, shiftSize]);
  useEffect(() => {
    fetchVacations();
  }, [vacationMonth]);
  useEffect(() => {
    fetchTimetable();
  }, [currentMonth]);

  // Когда меняются selectedDutyDays — синхронизируем currentMonth
  useEffect(() => {
    if (selectedDutyDays.length > 0) {
      const month = selectedDutyDays[0].slice(0, 7);
      if (month !== currentMonth) setCurrentMonth(month);
    }
  }, [selectedDutyDays, currentMonth]);

  const handleAssignmentChange = async (date, oldId, newId) => {
    const { startDate, endDate } = getMonthRange(currentMonth);
    setActiveEditPopover(null);
    setActiveAddUserPopover(null);
    try {
      await api.post(
        "/duties/assign/",
        { user_id_prev: oldId, user_id_new: newId, date },
        { params: { start_date: startDate, end_date: endDate } }
      );
      await fetchTimetable();
    } catch (err) {
      if (err.response?.status === 400) {
        const data = err.response.data;
        setError(
          typeof data === "string"
            ? data
            : data.detail || data.error || data.message || "Failed to update assignment"
        );
      } else {
        setError("Failed to update assignment");
      }
    }
  };

  const handleDeleteVacation = async (id) => {
    try {
      await api.delete(`/days-off/${id}/`);
      await fetchVacations();
    } catch {
      setError("Failed to delete");
    }
  };

  const handleGenerate = async () => {
    setIsDistributing(true);
    setError(null);
    setWarnings([]);
    setHighlightedDates(new Set());
    setSelectedDutyDays([]);
    try {
      const res = await api.post("/duties/generate/", {
        month: currentMonth,
        people_per_day: Number.parseInt(shiftSize, 10),
        dates: selectedDutyDays,
      });
      await fetchTimetable();
      const errors = res.data?.errors || {};
      const warningMessages = [];
      const datesToHighlight = new Set();
      Object.entries(errors).forEach(([date, messages]) => {
        if (messages?.length) {
          messages.forEach((msg) => warningMessages.push(msg));
          datesToHighlight.add(date);
        }
      });
      if (warningMessages.length > 0) {
        setWarnings(warningMessages);
        setHighlightedDates(datesToHighlight);
        setTimeout(() => setHighlightedDates(new Set()), 5000);
        setTimeout(() => setWarnings([]), 10000);
      }
    } catch (err) {
      if (err.response?.status === 400) {
        const data = err.response.data;
        let msg = "Generation failed";
        if (typeof data === "string") msg = data;
        else if (data.detail) msg = data.detail;
        else if (data.error) msg = data.error;
        else if (data.message) msg = data.message;
        else {
          const first = Object.values(data).find((v) => v);
          if (first) msg = Array.isArray(first) ? first[0] : first;
        }
        setError(msg);
      } else {
        setError("Generation failed");
      }
    } finally {
      setIsDistributing(false);
    }
  };

  useEffect(() => {
    const clickOut = (e) => {
      if (editRef.current && !editRef.current.contains(e.target)) setActiveEditPopover(null);
      if (addUserRef.current && !addUserRef.current.contains(e.target))
        setActiveAddUserPopover(null);
    };
    document.addEventListener("mousedown", clickOut);
    return () => document.removeEventListener("mousedown", clickOut);
  }, []);

  const displayDates = Array.from(new Set([...Object.keys(timetable), ...selectedDutyDays])).sort(
    (a, b) => new Date(a) - new Date(b)
  );

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Error banner */}
        {error && (
          <div className="sticky top-0 z-[300] bg-red-50 border-b-2 border-red-200 text-red-700 p-4 rounded-2xl shadow-lg flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-1">
              <AlertCircle size={20} className="flex-shrink-0" />
              <span className="font-bold text-sm">{error}</span>
            </div>
            <button
              type="button"
              onClick={() => setError(null)}
              className="p-1.5 hover:bg-red-100 rounded-lg transition-colors cursor-pointer"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Warnings banner */}
        {warnings.length > 0 && (
          <div className="sticky top-0 z-[300]">
            <div className="bg-yellow-50 border-2 border-yellow-200 text-yellow-800 p-4 rounded-2xl shadow-lg">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Info size={20} className="flex-shrink-0" />
                    <span className="font-bold text-sm">Generation warnings:</span>
                  </div>
                  <div className="space-y-1 ml-8">
                    {warnings.map((w, idx) => (
                      <div key={idx} className="text-sm">
                        • {w}
                      </div>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => setWarnings([])}
                  className="p-1.5 hover:bg-yellow-100 rounded-lg transition-colors cursor-pointer"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <header className="flex justify-between items-center bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
          <h1 className="text-2xl font-black text-slate-800">
            Duty<span className="text-blue-600">Planner</span>
          </h1>
          <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest bg-slate-50 px-4 py-2 rounded-full border border-slate-100">
            Control Panel v2.1
          </div>
        </header>

        {/* ① Staff — full width */}
        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-visible">
          <div className="p-5 border-b border-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">

              {/* Left: title + tabs */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 font-bold text-slate-700">
                <Users size={18} className="text-blue-600" /> Staff and Days Off
              </div>
              {/* Tabs */}
              <div className="flex items-center bg-slate-50 rounded-xl border border-slate-100 p-0.5 gap-0.5">
                <button
                  onClick={() => setStaffTab("staff")}
                  className={[
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer",
                    staffTab === "staff"
                      ? "bg-white text-blue-600 shadow-sm"
                      : "text-slate-400 hover:text-slate-600",
                  ].join(" ")}
                >
                  <Users size={12} /> Days Off
                </button>
                <button
                  onClick={() => setStaffTab("analytics")}
                  className={[
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer",
                    staffTab === "analytics"
                      ? "bg-white text-blue-600 shadow-sm"
                      : "text-slate-400 hover:text-slate-600",
                  ].join(" ")}
                >
                  <Users size={12} /> Analytics
                </button>
              </div>
            </div>

            {/* Right: month navigator — always reserve space */}
            <div className="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-100 w-fit" style={{ visibility: staffTab !== "staff" ? "hidden" : "visible" }}>
              <button
                onClick={() => setVacationMonth((m) => shiftMonth(m, -1))}
                className="p-1.5 hover:bg-white rounded-lg text-slate-400 hover:text-blue-600 transition-all cursor-pointer"
              >
                <ChevronLeft size={16} />
              </button>
              <div className="w-[140px] text-center text-[11px] font-black uppercase text-slate-600 tracking-tight">
                {new Date(`${vacationMonth}-01`).toLocaleDateString("en-US", {
                  month: "long",
                  year: "numeric",
                })}
              </div>
              <button
                onClick={() => setVacationMonth((m) => shiftMonth(m, 1))}
                className="p-1.5 hover:bg-white rounded-lg text-slate-400 hover:text-blue-600 transition-all cursor-pointer"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          {/* Tab content */}
          {staffTab === "analytics" ? (
            <DutyAnalyticsTab users={users} api={api} />
          ) : (
            <div className="overflow-visible px-2 pb-2">
            <table className="w-full text-left border-separate border-spacing-y-1">
              <thead>
                <tr className="text-[10px] uppercase font-black text-slate-400">
                  <th className="px-6 py-3 w-0 whitespace-nowrap">Employee</th>
                  <th className="px-3 py-3 w-full">Days Off for Period</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="group">
                    <td className="px-6 py-3 whitespace-nowrap whitespace-nowrap bg-slate-50/30 group-hover:bg-slate-50 rounded-l-2xl transition-colors">
                      <div className="font-bold text-slate-800 text-sm truncate">
                        {u.full_name || u.name}
                      </div>
                      <div className="text-[11px] text-slate-400 truncate mt-0.5">{u.email}</div>
                    </td>
                    <td className="px-3 py-3 bg-slate-50/30 group-hover:bg-slate-50 rounded-r-2xl transition-colors overflow-visible">
                      <div className="flex flex-wrap gap-1.5 items-center">
                        {vacations
                          .filter((v) => v.user === u.id)
                          .map((v) => (
                            <div
                              key={v.id}
                              className="flex items-center gap-1 px-2 py-1 bg-white border border-slate-200 rounded-lg text-[10px] font-bold text-slate-600 shadow-sm"
                            >
                              {new Date(v.date).getDate()}{" "}
                              {new Date(v.date).toLocaleDateString("en-US", { month: "short" })}
                              <button
                                onClick={() => handleDeleteVacation(v.id)}
                                className="text-slate-300 hover:text-red-500 cursor-pointer"
                              >
                                <X size={10} />
                              </button>
                            </div>
                          ))}
                        <DaysOffPicker
                          userId={u.id}
                          onSuccess={fetchVacations}
                          api={api}
                          onError={setError}
                          existingDates={vacations
                            .filter((v) => v.user === u.id)
                            .map((v) => v.date)}
                          vacationMonth={vacationMonth}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
         )}
        </div>
        {/* ② Schedule — full width */}
        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 overflow-visible">
          {/* Block title */}
          <div className="flex items-center gap-2 font-bold text-slate-700 mb-4">
            <ClipboardList size={18} className="text-blue-600" />
            <span>
              Schedule
              <span className="text-blue-600 ml-1">for {currentMonthLabel}</span>
            </span>
          </div>

          {/* Controls row */}
          <div className="mt-10 mb-6">
            <h2 className="text-sm font-bold text-slate-700 uppercase text-xs tracking-widest border-b border-slate-50 pb-4 mb-4 ">
              Generation Parameters
            </h2>
            <div className="flex flex-wrap items-end justify-start gap-6 mb-8 pb-5 border-b border-slate-50">
              {/* Period */}
              <div className="flex flex-col items-center gap-1">
                <label className="text-[10px] font-black text-slate-400 uppercase">Period</label>
                <ScheduleDatePicker
                  selectedDates={selectedDutyDays}
                  onChange={setSelectedDutyDays}
                  currentMonth={currentMonth}
                  onMonthChange={(ym) => {
                    if (ym) setCurrentMonth(ym);
                  }}
                  existingDates={Object.keys(timetable)}
                />
              </div>

              {/* People per shift */}
              <div className="flex flex-col items-center gap-1">
                <label className="text-[10px] font-black text-slate-400 uppercase">
                  People / Shift
                </label>
                <div className="flex items-center bg-slate-50 border border-slate-100 rounded-2xl px-1 h-[38px]">
                  <button
                    onClick={() => setShiftSize(Math.max(1, shiftSize - 1))}
                    className="p-2 text-slate-400 hover:text-blue-600 font-black cursor-pointer"
                  >
                    −
                  </button>
                  <input
                    type="number"
                    value={shiftSize}
                    readOnly
                    className="w-10 bg-transparent border-0 text-center text-xs font-black text-slate-700 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                  />
                  <button
                    onClick={() => setShiftSize(Math.min(users.length || 99, shiftSize + 1))}
                    className="p-2 text-slate-400 hover:text-blue-600 font-black cursor-pointer"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Generate */}
              <div className="flex flex-col items-center gap-1">
                <label className="text-[10px] font-black text-slate-400 uppercase opacity-0 select-none">
                  _
                </label>
                <button
                  onClick={handleGenerate}
                  disabled={isDistributing || selectedDutyDays.length === 0}
                  className="flex items-center gap-2 px-5 py-2.5 bg-slate-900 text-white rounded-2xl font-black text-[11px] uppercase tracking-widest hover:bg-black transition-all disabled:opacity-30 shadow-xl shadow-slate-200 cursor-pointer h-[38px]"
                >
                  {isDistributing ? (
                    "Generating…"
                  ) : (
                    <>
                      <Play size={13} /> Generate Schedule
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Schedule grid */}
          {displayDates.length === 0 ? (
            <div className="py-16 text-center text-slate-300 font-bold text-sm">
              Select a period above to see the schedule
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {displayDates.map((date) => {
                const assigned = timetable[date] || [];
                const isHighlighted = highlightedDates.has(date);
                return (
                  <div
                    key={date}
                    className={`p-4 bg-white rounded-2xl shadow-sm hover:shadow-md transition-all relative overflow-visible ${
                      isHighlighted
                        ? "border-2 border-red-500 ring-2 ring-red-200 animate-pulse"
                        : "border border-slate-100"
                    }`}
                  >
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-[10px] font-black text-blue-600 uppercase">
                        {new Date(date).toLocaleDateString("en-US", { weekday: "short" })}
                      </span>
                      <div className="flex items-center gap-2">
                        {isHighlighted && <AlertCircle size={14} className="text-red-500" />}
                        <span className="text-xs font-black text-slate-700">
                          {new Date(date).getDate()}{" "}
                          {new Date(date).toLocaleDateString("en-US", { month: "short" })}
                        </span>
                        <div
                          className="relative"
                          ref={activeAddUserPopover === date ? addUserRef : null}
                        >
                          <button
                            onClick={() =>
                              setActiveAddUserPopover(activeAddUserPopover === date ? null : date)
                            }
                            className={`p-1.5 rounded-lg cursor-pointer ${activeAddUserPopover === date ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-50"}`}
                          >
                            <UserPlus size={14} />
                          </button>
                          {activeAddUserPopover === date && (
                            <div className="absolute top-full right-0 mt-2 w-56 bg-white border border-slate-200 shadow-2xl rounded-2xl z-[100] py-2">
                              {users
                                .filter((usr) => !assigned.some((au) => au.id === usr.id))
                                .map((usr) => (
                                  <button
                                    key={usr.id}
                                    onClick={() => handleAssignmentChange(date, null, usr.id)}
                                    className="w-full text-left px-4 py-2 text-[11px] hover:bg-blue-50 font-bold text-slate-700 transition-colors cursor-pointer"
                                  >
                                    {usr.full_name || usr.name}
                                  </button>
                                ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      {assigned.map((u) => (
                        <div
                          key={u.id}
                          className="group relative flex items-center justify-between bg-slate-50 p-2.5 rounded-xl text-[11px] font-bold text-slate-600"
                        >
                          <span className="truncate pr-2">{u.name}</span>
                          <div className="flex gap-1">
                            <button
                              onClick={() =>
                                setActiveEditPopover(
                                  activeEditPopover === `${date}-${u.id}` ? null : `${date}-${u.id}`
                                )
                              }
                              className="p-1 hover:bg-blue-100 rounded-md text-blue-400 cursor-pointer"
                            >
                              <RotateCcw size={12} />
                            </button>
                            <button
                              onClick={() => handleAssignmentChange(date, u.id, null)}
                              className="p-1 hover:bg-red-100 rounded-md text-red-400 cursor-pointer"
                            >
                              <X size={12} />
                            </button>
                          </div>
                          {activeEditPopover === `${date}-${u.id}` && (
                            <div
                              ref={editRef}
                              className="absolute bottom-full left-0 w-full mb-1 bg-white border border-slate-200 shadow-2xl rounded-xl z-[100] py-1 max-h-48 overflow-y-auto"
                            >
                              {users
                                .filter((usr) => !assigned.some((au) => au.id === usr.id))
                                .map((usr) => (
                                  <button
                                    key={usr.id}
                                    onClick={() => handleAssignmentChange(date, u.id, usr.id)}
                                    className="w-full text-left px-3 py-2 text-[11px] hover:bg-blue-100 font-bold cursor-pointer"
                                  >
                                    {usr.full_name || usr.name}
                                  </button>
                                ))}
                            </div>
                          )}
                        </div>
                      ))}
                      {assigned.length === 0 && (
                        <div className="py-2 text-center text-[9px] text-slate-300 font-bold italic">
                          No assignment
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;