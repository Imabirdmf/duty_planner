import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Calendar, Users, Play, X, Info, ClipboardList,
  Plus, AlertCircle, UserPlus, RotateCcw, ChevronLeft, ChevronRight,
  CalendarDays
} from 'lucide-react';

const API_URL = import.meta.env.PROD
  ? ''
  : (import.meta.env.VITE_API_URL || 'http://localhost:8000');

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 5000,
});

const App = () => {
  // Состояние для генерации графика (Блок Параметры)
  const [currentMonth, setCurrentMonth] = useState(new Date().toISOString().slice(0, 7));
  // Состояние для управления выходными (Блок Сотрудники)
  const [vacationMonth, setVacationMonth] = useState(new Date().toISOString().slice(0, 7));

  const [shiftSize, setShiftSize] = useState(2);
  const [users, setUsers] = useState([]);
  const [vacations, setVacations] = useState([]);
  const [selectedDutyDays, setSelectedDutyDays] = useState([]);
  const [timetable, setTimetable] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isDistributing, setIsDistributing] = useState(false);
  const [error, setError] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [highlightedDates, setHighlightedDates] = useState(new Set());

  // Поповеры
  const [activeVacationPopover, setActiveVacationPopover] = useState(null);
  const [activeEditPopover, setActiveEditPopover] = useState(null);
  const [activeAddUserPopover, setActiveAddUserPopover] = useState(null);
  const [isMonthPickerOpen, setIsMonthPickerOpen] = useState(false);

  const vacationRef = useRef(null);
  const editRef = useRef(null);
  const addUserRef = useRef(null);
  const monthPickerRef = useRef(null);

  // --- Вспомогательные функции ---
  const getMonthRange = (monthStr) => {
    const [year, month] = monthStr.split('-').map(Number);
    const startDate = `${monthStr}-01`;
    const lastDay = new Date(year, month, 0).getDate();
    const endDate = `${monthStr}-${lastDay.toString().padStart(2, '0')}`;
    return { startDate, endDate };
  };

  const getDaysInMonth = (monthStr) => {
    const [year, month] = monthStr.split('-').map(Number);
    const days = new Date(year, month, 0).getDate();
    return Array.from({ length: days }, (_, i) => `${monthStr}-${(i + 1).toString().padStart(2, '0')}`);
  };

  const shiftMonth = (current, offset) => {
    const [year, month] = current.split('-').map(Number);
    const date = new Date(year, month - 1 + offset, 1);

    const newYear = date.getFullYear();
    const newMonth = String(date.getMonth() + 1).padStart(2, '0');

    return `${newYear}-${newMonth}`;
  };

  // --- API запросы ---
  const fetchUsers = async () => {
    try {
      const res = await api.get('/users/');
      setUsers(res.data);
    } catch { setError("Failed to load users"); }
  };

  const fetchVacations = async () => {
    const { startDate, endDate } = getMonthRange(vacationMonth);
    try {
      const res = await api.get('/days-off/', { params: { start_date: startDate, end_date: endDate } });
      setVacations(res.data);
    } catch (err) {
        if (err.response) {
            switch (err.response.status) {
                case 404:
                    setVacations([]);
                    break;
                default:
                    setError("Failed to load days off");
            }
        }
    }
  };

  const fetchTimetable = async () => {
    const { startDate, endDate } = getMonthRange(currentMonth);
    try {
      const res = await api.get('/duties/list_assignments/', { params: { start_date: startDate, end_date: endDate } });
      const items = res.data?.data || res.data;
      if (Array.isArray(items)) {
        const mapped = items.reduce((acc, item) => {
          acc[item.date] = item.users.map(u => ({ id: u.id, name: u.full_name || u.name }));
          return acc;
        }, {});
        setTimetable(mapped);
      }
    } catch { setTimetable({}); }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    fetchVacations();
  }, [vacationMonth]);

  useEffect(() => {
    fetchTimetable();
    setSelectedDutyDays([]);
  }, [currentMonth]);

  const handleAssignmentChange = async (date, oldId, newId) => {
    const { startDate, endDate } = getMonthRange(currentMonth);
    setActiveEditPopover(null);
    setActiveAddUserPopover(null);
    try {
      await api.post(`/duties/assign/`,
        { user_id_prev: oldId, user_id_new: newId, date },
        { params: { start_date: startDate, end_date: endDate } }
      );
      await fetchTimetable();
    } catch { setError("Failed to update assignment"); }
  };

  const handleAddVacation = async (userId, date) => {
    setError(null);
    try {
      await api.post('/days-off/', { user: userId, date });
      await fetchVacations();
      setActiveVacationPopover(null);
    } catch (err) {
      if (err.response && err.response.data) {
        const data = err.response.data;
        if (data.non_field_errors) {
          setError(data.non_field_errors[0]);
        } else if (data.date) {
          setError(`Date error: ${data.date[0]}`);
        } else {
          setError("Failed to add day off");
        }
      } else {
        setError("Server connection error");
      }

      setTimeout(() => setError(null), 5000);
    }
  };

  const handleDeleteVacation = async (id) => {
    try {
      await api.delete(`/days-off/${id}/`);
      await fetchVacations();
    } catch { setError("Failed to delete"); }
  };

  useEffect(() => {
    const clickOut = (e) => {
      if (vacationRef.current && !vacationRef.current.contains(e.target)) setActiveVacationPopover(null);
      if (editRef.current && !editRef.current.contains(e.target)) setActiveEditPopover(null);
      if (addUserRef.current && !addUserRef.current.contains(e.target)) setActiveAddUserPopover(null);
      if (monthPickerRef.current && !monthPickerRef.current.contains(e.target)) setIsMonthPickerOpen(false);
    };
    document.addEventListener('mousedown', clickOut);
    return () => document.removeEventListener('mousedown', clickOut);
  }, []);

  const displayDates = Array.from(new Set([...Object.keys(timetable), ...selectedDutyDays])).sort();

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Error popup */}
        {error && (
          <div className="sticky top-0 left-0 right-0 z-[300] bg-red-50 border-b-2 border-red-200 text-red-700 p-4 rounded-2xl shadow-lg flex items-center justify-between gap-4 animate-in fade-in slide-in-from-top-4">
            <div className="flex items-center gap-3 flex-1">
              <AlertCircle size={20} className="flex-shrink-0" />
              <span className="font-bold text-sm">{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="p-1.5 hover:bg-red-100 rounded-lg transition-colors flex-shrink-0"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Warning popup */}
        {warnings.length > 0 && (
          <div className="sticky top-0 z-[300] p-4 animate-in fade-in slide-in-from-top-4">
            <div className="max-w-7xl mx-auto bg-yellow-50 border-2 border-yellow-200 text-yellow-800 p-4 rounded-2xl shadow-lg">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Info size={20} className="flex-shrink-0" />
                    <span className="font-bold text-sm">Generation warnings:</span>
                  </div>
                  <div className="space-y-1 ml-8">
                    {warnings.map((warning, idx) => (
                      <div key={idx} className="text-sm">
                        • {warning}
                      </div>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => setWarnings([])}
                  className="p-1.5 hover:bg-yellow-100 rounded-lg transition-colors flex-shrink-0"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          </div>
        )}


        <header className="flex justify-between items-center bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
          <h1 className="text-2xl font-black text-slate-800">Duty<span className="text-blue-600">Planner</span></h1>
          <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest bg-slate-50 px-4 py-2 rounded-full border border-slate-100">
            Control Panel v2.1
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

          <div className="lg:col-span-8 space-y-6">

            {/* Staff Block */}
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-visible">
              <div className="p-5 border-b border-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-2 font-bold text-slate-700">
                  <Users size={18} className="text-blue-600" /> Staff and Days Off
                </div>

                {/* Period selector for days off */}
                <div className="flex items-center gap-1 bg-slate-50 p-1 rounded-xl border border-slate-100 w-fit">
                  <button onClick={() => setVacationMonth(m => shiftMonth(m, -1))} className="p-1.5 hover:bg-white rounded-lg text-slate-400 hover:text-blue-600 transition-all"><ChevronLeft size={16}/></button>
                  <div className="w-[140px] text-center text-[11px] font-black uppercase text-slate-600 tracking-tight">
                    {new Date(vacationMonth).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                  </div>
                  <button onClick={() => setVacationMonth(m => shiftMonth(m, 1))} className="p-1.5 hover:bg-white rounded-lg text-slate-400 hover:text-blue-600 transition-all"><ChevronRight size={16}/></button>
                </div>
              </div>

              <div className="overflow-visible px-2 pb-2">
                <table className="w-full text-left table-fixed border-separate border-spacing-y-1">
                  <thead>
                    <tr className="text-[10px] uppercase font-black text-slate-400">
                      <th className="px-6 py-3 w-1/3">Employee</th>
                      <th className="px-6 py-3 w-2/3">Days Off for Period</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(u => (
                      <tr key={u.id} className="group">
                        <td className="px-6 py-3 bg-slate-50/30 group-hover:bg-slate-50 rounded-l-2xl transition-colors">
                          <div className="font-bold text-slate-800 text-sm truncate">{u.full_name || u.name}</div>
                        </td>
                        <td className="px-6 py-3 bg-slate-50/30 group-hover:bg-slate-50 rounded-r-2xl transition-colors overflow-visible">
                          <div className="flex flex-wrap gap-1.5 items-center">
                            {vacations.filter(v => v.user === u.id).map(v => (
                              <div key={v.id} className="flex items-center gap-1 px-2 py-1 bg-white border border-slate-200 rounded-lg text-[10px] font-bold text-slate-600 shadow-sm">
                                {new Date(v.date).getDate()} {new Date(v.date).toLocaleDateString('en-US', {month:'short'})}
                                <button onClick={() => handleDeleteVacation(v.id)} className="text-slate-300 hover:text-red-500"><X size={10}/></button>
                              </div>
                            ))}
                            <div className="relative" ref={activeVacationPopover === u.id ? vacationRef : null}>
                              <button onClick={() => setActiveVacationPopover(activeVacationPopover === u.id ? null : u.id)} className={`p-1.5 border rounded-lg transition-all ${activeVacationPopover === u.id ? 'bg-blue-600 text-white border-blue-600 shadow-lg' : 'border-dashed border-slate-200 text-slate-400 hover:border-blue-300'}`}><Plus size={14}/></button>
                              {activeVacationPopover === u.id && (
                                <div className="absolute right-0 top-full mt-2 z-[100] bg-white border border-slate-200 shadow-2xl rounded-2xl p-4 w-64 animate-in zoom-in-95">
                                  <div className="text-[10px] font-black uppercase text-blue-600 mb-3 text-center border-b pb-2 border-slate-50">
                                    {new Date(vacationMonth).toLocaleDateString('en-US', {month: 'long', year: 'numeric'})}
                                  </div>
                                  <div className="grid grid-cols-7 gap-1">
                                    {getDaysInMonth(vacationMonth).map(d => (
                                      <button key={d} onClick={() => handleAddVacation(u.id, d)} className="aspect-square rounded-lg text-[10px] font-bold hover:bg-blue-50 text-slate-600 border border-transparent hover:border-blue-100">{parseInt(d.split('-')[2])}</button>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Schedule Grid */}
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 overflow-visible">
              <div className="flex items-center gap-2 mb-6 font-bold text-slate-700">
                <ClipboardList size={18} className="text-blue-600" /> Schedule for {new Date(currentMonth).toLocaleDateString('en-US', {month:'long'})}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {displayDates.map((date) => {
                  const assigned = timetable[date] || [];
                  const isHighlighted = highlightedDates.has(date);

                  return (
                    <div
                      key={date}
                      className={`p-4 bg-white rounded-2xl shadow-sm hover:shadow-md transition-all relative overflow-visible ${
                        isHighlighted
                          ? 'border-2 border-red-500 ring-2 ring-red-200 animate-pulse'
                          : 'border border-slate-100'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-[10px] font-black text-blue-600 uppercase">
                          {new Date(date).toLocaleDateString('en-US', {weekday:'short'})}
                        </span>
                        <div className="flex items-center gap-2">
                          {isHighlighted && (
                            <AlertCircle size={14} className="text-red-500" />
                          )}
                          <span className="text-xs font-black text-slate-700">
                            {new Date(date).getDate()} {new Date(date).toLocaleDateString('en-US', {month:'short'})}
                          </span>
                          <div className="relative" ref={activeAddUserPopover === date ? addUserRef : null}>
                            <button onClick={() => setActiveAddUserPopover(activeAddUserPopover === date ? null : date)} className={`p-1.5 rounded-lg ${activeAddUserPopover === date ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-50'}`}><UserPlus size={14}/></button>
                            {activeAddUserPopover === date && (
                              <div className="absolute top-full right-0 mt-2 w-56 bg-white border border-slate-200 shadow-2xl rounded-2xl z-[100] py-2 animate-in fade-in slide-in-from-top-2">
                                {users.filter(usr => !assigned.some(au => au.id === usr.id)).map(usr => (
                                  <button key={usr.id} onClick={() => handleAssignmentChange(date, null, usr.id)} className="w-full text-left px-4 py-2 text-[11px] hover:bg-blue-50 font-bold text-slate-700 transition-colors">{usr.full_name || usr.name}</button>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        {assigned.map(u => (
                          <div key={u.id} className="group relative flex items-center justify-between bg-slate-50 p-2.5 rounded-xl text-[11px] font-bold text-slate-600">
                            <span className="truncate pr-2">{u.name}</span>
                            <div className="flex gap-1">
                              <button onClick={() => setActiveEditPopover(activeEditPopover === `${date}-${u.id}` ? null : `${date}-${u.id}`)} className="p-1 hover:bg-blue-100 rounded-md text-blue-400"><RotateCcw size={12}/></button>
                              <button onClick={() => handleAssignmentChange(date, u.id, null)} className="p-1 hover:bg-red-100 rounded-md text-red-400"><X size={12}/></button>
                            </div>
                            {activeEditPopover === `${date}-${u.id}` && (
                              <div ref={editRef} className="absolute bottom-full left-0 w-full mb-1 bg-white border border-slate-200 shadow-2xl rounded-xl z-[100] py-1 max-h-48 overflow-y-auto">
                                {users.filter(usr => !assigned.some(au => au.id === usr.id)).map(usr => (
                                  <button key={usr.id} onClick={() => handleAssignmentChange(date, u.id, usr.id)} className="w-full text-left px-3 py-2 text-[11px] hover:bg-blue-100 font-bold">{usr.full_name || usr.name}</button>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                        {assigned.length === 0 && <div className="py-2 text-center text-[9px] text-slate-300 font-bold italic">No assignment</div>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Parameters */}
          <div className="lg:col-span-4 space-y-6">
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 sticky top-8 z-10 overflow-visible">
              <div className="flex items-center gap-2 font-bold text-slate-700 border-b border-slate-50 pb-4 mb-6 uppercase text-xs tracking-widest">
                <CalendarDays size={18} className="text-blue-600" /> Generation Parameters
              </div>

              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4 overflow-visible">

                  {/* Period selector for generation */}
                  <div className="space-y-1.5 relative" ref={monthPickerRef}>
                    <label className="text-[10px] font-black text-slate-400 uppercase">Period</label>
                    <button onClick={() => setIsMonthPickerOpen(!isMonthPickerOpen)} className="w-full flex justify-between items-center bg-slate-50 border border-slate-100 p-3 text-[11px] rounded-2xl font-black transition-all hover:bg-slate-100">
                      <span className="capitalize">{new Date(currentMonth).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}</span>
                      <Calendar size={14} className="text-blue-500" />
                    </button>
                    {isMonthPickerOpen && (
                      <div className="absolute top-full left-0 w-64 mt-2 bg-white border border-slate-200 shadow-2xl rounded-2xl p-3 z-[150] animate-in zoom-in-95">
                        <div className="grid grid-cols-3 gap-1">
                          {["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].map((m, i) => (
                            <button key={`m-${i}`} onClick={() => {setCurrentMonth(`${currentMonth.split('-')[0]}-${(i+1).toString().padStart(2,'0')}`); setIsMonthPickerOpen(false);}} className="py-2 text-[10px] font-black uppercase rounded-lg hover:bg-blue-50 hover:text-blue-600 transition-colors">{m}</button>
                          ))}
                        </div>
                        <div className="mt-2 pt-2 border-t border-slate-50 flex justify-between">
                           <button onClick={() => setCurrentMonth(m => shiftMonth(m, -12))} className="text-[9px] font-bold text-slate-400 hover:text-slate-600">Previous Year</button>
                           <button onClick={() => setCurrentMonth(m => shiftMonth(m, 12))} className="text-[9px] font-bold text-slate-400 hover:text-slate-600">Next Year</button>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase">People per Shift</label>
                    <div className="flex items-center bg-slate-50 border border-slate-100 rounded-2xl px-1">
                      <button onClick={() => setShiftSize(Math.max(1, shiftSize-1))} className="p-2 text-slate-400 hover:text-blue-600 font-black">-</button>
                      <input type="number" value={shiftSize} readOnly className="w-full bg-transparent border-0 text-center text-xs font-black text-slate-700" />
                      <button onClick={() => setShiftSize(shiftSize+1)} className="p-2 text-slate-400 hover:text-blue-600 font-black">+</button>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="text-[10px] font-black text-slate-400 uppercase">Days to Schedule</label>
                  <div className="grid grid-cols-7 gap-1 bg-slate-50/50 p-2 rounded-2xl border border-slate-100">
                    {getDaysInMonth(currentMonth).map((d) => (
                      <button key={`sel-day-${d}`} onClick={() => setSelectedDutyDays(prev => prev.includes(d) ? prev.filter(x => x!==d) : [...prev, d])} className={`aspect-square rounded-lg text-[10px] font-bold transition-all border ${selectedDutyDays.includes(d) ? 'bg-blue-600 text-white border-blue-600 shadow-md scale-105' : 'bg-white text-slate-400 border-slate-100 hover:border-blue-200 hover:text-blue-400'}`}>
                        {parseInt(d.split('-')[2])}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={async () => {
                    setIsDistributing(true);
                    setError(null);
                    setWarnings([]);
                    setHighlightedDates(new Set());

                    try {
                      const res = await api.post('/duties/generate/', {
                        month: currentMonth,
                        people_per_day: parseInt(shiftSize),
                        dates: selectedDutyDays
                      });

                      const items = res.data?.data || res.data;
                      const errors = res.data?.errors || {};

                      // Process schedule data
                      if (Array.isArray(items)) {
                        const mapped = items.reduce((acc, item) => {
                          acc[item.date] = item.users.map(u => ({
                            id: u.id,
                            name: u.full_name || u.name
                          }));
                          return acc;
                        }, {});
                        setTimetable(mapped);
                      }

                      // Process errors
                      const warningMessages = [];
                      const datesToHighlight = new Set();

                      Object.entries(errors).forEach(([date, messages]) => {
                        if (messages && messages.length > 0) {
                          messages.forEach(msg => warningMessages.push(msg));
                          datesToHighlight.add(date);
                        }
                      });

                      if (warningMessages.length > 0) {
                        setWarnings(warningMessages);
                        setHighlightedDates(datesToHighlight);

                        // Auto-hide highlight after 5 seconds
                        setTimeout(() => {
                          setHighlightedDates(new Set());
                        }, 5000);

                        // Auto-hide warnings after 10 seconds
                        setTimeout(() => {
                          setWarnings([]);
                        }, 10000);
                      }

                    } catch {
                      setError("Generation failed");
                    } finally {
                      setIsDistributing(false);
                    }
                  }}
                  disabled={isDistributing || selectedDutyDays.length === 0}
                  className="w-full py-4 bg-slate-900 text-white rounded-2xl font-black text-[11px] uppercase tracking-widest hover:bg-black transition-all disabled:opacity-30 shadow-xl shadow-slate-200 flex items-center justify-center gap-2"
                >
                  {isDistributing ? 'Generating...' : ( <><Play size={14}/> Generate Schedule</> )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;