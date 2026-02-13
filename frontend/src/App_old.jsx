import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Calendar, Users, Play, X, Info, ClipboardList,
  Plus, AlertCircle, UserPlus, RotateCcw, ChevronLeft, ChevronRight
} from 'lucide-react';

// Настройка API клиента
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000,
});

const App = () => {
  // --- Состояния приложения ---
  const [currentMonth, setCurrentMonth] = useState(new Date().toISOString().slice(0, 7));
  const [shiftSize, setShiftSize] = useState(2);
  const [users, setUsers] = useState([]);
  const [vacations, setVacations] = useState([]);
  const [selectedDutyDays, setSelectedDutyDays] = useState([]);
  const [timetable, setTimetable] = useState(null);

  // Состояния интерфейса
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [isDistributing, setIsDistributing] = useState(false);
  const [error, setError] = useState(null);

  // Состояния для поповеров (выпадающих списков)
  const [activeVacationPopover, setActiveVacationPopover] = useState(null);
  const [activeEditPopover, setActiveEditPopover] = useState(null);

  // Рефы для отслеживания кликов вне элементов
  const vacationRef = useRef(null);
  const editRef = useRef(null);

  // --- Эффекты ---

  // Обработка Esc и кликов вне поповеров
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (vacationRef.current && !vacationRef.current.contains(event.target)) {
        setActiveVacationPopover(null);
      }
      if (editRef.current && !editRef.current.contains(event.target)) {
        setActiveEditPopover(null);
      }
    };

    const handleEsc = (event) => {
      if (event.key === 'Escape') {
        setActiveVacationPopover(null);
        setActiveEditPopover(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEsc);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEsc);
    };
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchTimetable();
    // При смене месяца сбрасываем выбранные даты
    setSelectedDutyDays([]);
  }, [currentMonth]);

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
    return Array.from({ length: days }, (_, i) => {
      const day = i + 1;
      return `${monthStr}-${day.toString().padStart(2, '0')}`;
    });
  };

  const transformDuties = (response) => {
    const items = response.data?.data || response.data;
    if (!items || !Array.isArray(items)) return null;

    return items.reduce((acc, item) => {
      acc[item.date] = item.users.map(u => ({
        id: u.id,
        name: u.full_name || u.name
      }));
      return acc;
    }, {});
  };

  // --- API запросы ---

  const fetchInitialData = async () => {
    setIsLoadingUsers(true);
    try {
      const [usersRes, vacationsRes] = await Promise.all([
        api.get('/api/users/'),
        api.get('/api/days-off/')
      ]);
      setUsers(usersRes.data);
      setVacations(vacationsRes.data);
    } catch (err) {
      setError("Ошибка связи с сервером.");
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const fetchTimetable = async () => {
    const { startDate, endDate } = getMonthRange(currentMonth);
    try {
      const res = await api.get(`/api/duties/list_assignments/`, {
        params: { start_date: startDate, end_date: endDate }
      });
      setTimetable(transformDuties(res));
    } catch (err) {
      console.error("Не удалось загрузить расписание");
    }
  };

  const handleAddVacation = async (userId, date) => {
    if (!date) return;
    try {
      const res = await api.post('/api/days-off/', { user: userId, date });
      setVacations(prev => [...prev, res.data]);
      setActiveVacationPopover(null);
      setError(null);
    } catch (err) {
      // Обработка специфических ошибок бэкенда
      if (err.response && err.response.data) {
        const data = err.response.data;
        if (data.non_field_errors) {
          setError(data.non_field_errors[0]);
        } else if (data.date) {
          setError(`Ошибка даты: ${data.date[0]}`);
        } else {
          setError("Не удалось добавить выходной.");
        }
      } else {
        setError("Ошибка связи с сервером.");
      }
    }
  };

  const handleDeleteVacation = async (id) => {
    try {
      await api.delete(`/api/days-off/${id}/`);
      setVacations(prev => prev.filter(v => v.id !== id));
    } catch (err) {
      setError("Ошибка удаления записи.");
    }
  };

  const handleGenerate = async () => {
    if (selectedDutyDays.length === 0) return;
    setIsDistributing(true);
    try {
      const res = await api.post('/api/duties/generate/', {
        month: currentMonth,
        people_per_day: parseInt(shiftSize),
        dates: selectedDutyDays
      });
      setTimetable(transformDuties(res));
      setError(null);
    } catch (err) {
      setError("Ошибка генерации расписания.");
    } finally {
      setIsDistributing(false);
    }
  };

  const handleAssignmentChange = async (date, oldUserId, newUserId) => {
    const { startDate, endDate } = getMonthRange(currentMonth);
    setActiveEditPopover(null);
    try {
      await api.post(`/api/duties/assign/`, {
        user_id_prev: oldUserId,
        user_id_new: newUserId,
        date: date
      }, {
        params: { start_date: startDate, end_date: endDate }
      });
      await fetchTimetable();
      setError(null);
    } catch (err) {
      setError("Ошибка обновления назначения.");
    }
  };

  const toggleDaySelection = (dateStr) => {
    setSelectedDutyDays(prev =>
      prev.includes(dateStr) ? prev.filter(d => d !== dateStr) : [...prev, dateStr]
    );
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 font-sans p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl flex items-center justify-between sticky top-4 z-50 shadow-lg animate-in fade-in slide-in-from-top-4">
            <div className="flex items-center gap-2 font-medium">
              <AlertCircle size={18} /> {error}
            </div>
            <button onClick={() => setError(null)} className="p-1 hover:bg-red-100 rounded-lg transition-colors"><X size={18} /></button>
          </div>
        )}

        <header className="flex flex-col md:flex-row justify-between items-center bg-white p-6 rounded-3xl shadow-sm border border-slate-100 gap-4">
          <div>
            <h1 className="text-2xl font-black text-slate-800 tracking-tight">Duty<span className="text-blue-600">Planner</span></h1>
            <p className="text-slate-400 text-sm font-medium uppercase tracking-widest">Team Management System</p>
          </div>
          <div className="flex items-center gap-4 bg-slate-50 p-2 rounded-2xl">
             <div className="px-4 py-2 text-xs font-black text-slate-500">
               {new Date(currentMonth).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
             </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Левая колонка: Команда и Расписание */}
          <div className="lg:col-span-8 space-y-6">
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
              <div className="p-5 border-b border-slate-50 flex items-center gap-2 font-bold text-slate-700">
                <Users size={18} className="text-blue-600" /> Состав команды
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-50/50">
                    <tr className="text-[10px] uppercase font-black text-slate-400">
                      <th className="px-6 py-4">Сотрудник</th>
                      <th className="px-6 py-4">Выходные дни</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {users.map(u => (
                      <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-bold text-slate-800">{u.full_name || u.name}</div>
                          <div className="text-[11px] text-slate-400">{u.email}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-wrap gap-2 items-center">
                            {vacations.filter(v => v.user === u.id).map(v => (
                              <div key={v.id} className="flex items-center gap-1.5 px-3 py-1 bg-blue-50 border border-blue-100 rounded-xl text-[10px] font-bold text-blue-600">
                                {new Date(v.date).toLocaleDateString('ru-RU', {day:'numeric', month:'short'})}
                                <button onClick={() => handleDeleteVacation(v.id)} className="hover:text-red-500 transition-colors"><X size={12} /></button>
                              </div>
                            ))}
                            <div className="relative" ref={activeVacationPopover === u.id ? vacationRef : null}>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setActiveVacationPopover(activeVacationPopover === u.id ? null : u.id);
                                }}
                                className="p-1.5 border border-dashed border-slate-200 text-slate-400 rounded-xl hover:border-blue-400 hover:text-blue-500 transition-all"
                              >
                                <Plus size={14} />
                              </button>
                              {activeVacationPopover === u.id && (
                                <div className="absolute left-0 top-full mt-2 z-20 bg-white border border-slate-100 shadow-2xl rounded-2xl p-3 w-48 animate-in fade-in zoom-in duration-150">
                                  <label className="block text-[9px] font-black uppercase text-slate-400 mb-2">Выберите дату</label>
                                  <input
                                    type="date"
                                    className="w-full text-xs font-bold p-2 bg-slate-50 rounded-lg outline-none border border-slate-100 focus:border-blue-400"
                                    onChange={(e) => handleAddVacation(u.id, e.target.value)}
                                  />
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

            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
              <div className="flex items-center justify-between mb-6 font-bold text-slate-700">
                <div className="flex items-center gap-2">
                  <ClipboardList size={18} className="text-blue-600" /> Утвержденный график
                </div>
              </div>

              {!timetable ? (
                <div className="py-20 text-center space-y-4">
                  <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto">
                    <Calendar className="text-slate-200" size={32} />
                  </div>
                  <p className="text-slate-400 text-sm font-medium">Расписание еще не создано. <br/>Выберите даты в правой панели.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {Object.entries(timetable).sort().map(([date, assignedUsers]) => (
                    <div key={date} className="p-4 bg-white border border-slate-100 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-[10px] font-black text-blue-600 uppercase tracking-widest">
                          {new Date(date).toLocaleDateString('ru-RU', {weekday:'short'})}
                        </span>
                        <span className="text-xs font-black text-slate-700">
                          {new Date(date).toLocaleDateString('ru-RU', {day:'numeric', month:'long'})}
                        </span>
                      </div>
                      <div className="space-y-2">
                        {assignedUsers.map(u => (
                          <div key={u.id} className="group relative flex items-center justify-between bg-slate-50 p-2.5 rounded-xl text-[11px] font-bold text-slate-600">
                            <span className="truncate pr-2">{u.name}</span>
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setActiveEditPopover(activeEditPopover === `${date}-${u.id}` ? null : `${date}-${u.id}`);
                                }}
                                className="p-1 hover:bg-blue-100 rounded-md text-blue-400"
                              >
                                <RotateCcw size={12} />
                              </button>
                              <button onClick={() => handleAssignmentChange(date, u.id, null)} className="p-1 hover:bg-red-100 rounded-md text-red-400"><X size={12} /></button>
                            </div>

                            {activeEditPopover === `${date}-${u.id}` && (
                              <div ref={editRef} className="absolute top-full left-0 w-full mt-1 bg-white border border-slate-200 shadow-2xl rounded-xl z-30 py-1 max-h-48 overflow-y-auto animate-in fade-in slide-in-from-top-1">
                                <div className="px-3 py-1.5 text-[9px] text-slate-400 uppercase font-black border-b border-slate-50 bg-slate-50/50">Заменить на:</div>
                                {users.filter(usr => !assignedUsers.some(au => au.id === usr.id)).map(usr => (
                                  <button
                                    key={usr.id}
                                    onClick={() => handleAssignmentChange(date, u.id, usr.id)}
                                    className="w-full text-left px-3 py-2 text-[11px] hover:bg-blue-600 hover:text-white font-bold text-slate-900 transition-colors"
                                  >
                                    {usr.full_name || usr.name}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}

                        {assignedUsers.length < shiftSize && (
                          <div className="relative">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setActiveEditPopover(activeEditPopover === `${date}-new` ? null : `${date}-new`);
                              }}
                              className="w-full py-2 border border-dashed border-slate-200 rounded-xl text-[10px] font-bold text-slate-400 flex items-center justify-center gap-1 hover:text-blue-500 hover:border-blue-200 transition-all"
                            >
                              <UserPlus size={12} /> Добавить
                            </button>
                            {activeEditPopover === `${date}-new` && (
                              <div ref={editRef} className="absolute top-full left-0 w-full mt-1 bg-white border border-slate-200 shadow-2xl rounded-xl z-30 py-1 max-h-48 overflow-y-auto animate-in fade-in slide-in-from-top-1">
                                <div className="px-3 py-1.5 text-[9px] text-slate-400 uppercase font-black border-b border-slate-50 bg-slate-50/50">Выбрать:</div>
                                {users.filter(usr => !assignedUsers.some(au => au.id === usr.id)).map(usr => (
                                  <button
                                    key={usr.id}
                                    onClick={() => handleAssignmentChange(date, null, usr.id)}
                                    className="w-full text-left px-3 py-2 text-[11px] hover:bg-blue-600 hover:text-white font-bold text-slate-900 transition-colors"
                                  >
                                    {usr.full_name || usr.name}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Правая колонка: Настройки генерации */}
          <div className="lg:col-span-4 space-y-6">
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 sticky top-8">
              <div className="flex items-center gap-2 font-bold text-slate-700 border-b border-slate-50 pb-4 mb-6">
                <Calendar size={18} className="text-blue-600" /> Параметры
              </div>

              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Месяц</label>
                    <input
                      type="month"
                      value={currentMonth}
                      onChange={e => setCurrentMonth(e.target.value)}
                      className="w-full bg-slate-50 border-0 p-3 text-sm rounded-2xl font-bold outline-none ring-2 ring-transparent focus:ring-blue-100 transition-all"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider">На смену</label>
                    <input
                      type="number"
                      min="1"
                      value={shiftSize}
                      onChange={e => setShiftSize(e.target.value)}
                      className="w-full bg-slate-50 border-0 p-3 text-sm rounded-2xl font-bold outline-none ring-2 ring-transparent focus:ring-blue-100 transition-all"
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Дни дежурств</label>
                  </div>

                  <div className="grid grid-cols-7 gap-1">
                    {['Пн','Вт','Ср','Чт','Пт','Сб','Вс'].map(d => (
                      <div key={d} className="text-center text-[9px] font-black text-slate-300 py-1">{d}</div>
                    ))}
                    {/* Пустые ячейки для начала месяца */}
                    {Array.from({ length: (new Date(currentMonth + '-01').getDay() + 6) % 7 }).map((_, i) => (
                      <div key={`empty-${i}`} />
                    ))}
                    {getDaysInMonth(currentMonth).map(dateStr => {
                      const dayNum = dateStr.split('-')[2];
                      const isSelected = selectedDutyDays.includes(dateStr);
                      return (
                        <button
                          key={dateStr}
                          onClick={() => toggleDaySelection(dateStr)}
                          className={`
                            aspect-square rounded-lg text-[10px] font-bold transition-all
                            ${isSelected
                              ? 'bg-blue-600 text-white shadow-md shadow-blue-100'
                              : 'bg-slate-50 text-slate-400 hover:bg-slate-100'}
                          `}
                        >
                          {parseInt(dayNum)}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <button
                  onClick={handleGenerate}
                  disabled={isDistributing || selectedDutyDays.length === 0}
                  className="w-full py-4 bg-slate-900 text-white rounded-2xl font-black text-[11px] uppercase tracking-widest hover:bg-black transition-all flex items-center justify-center gap-3 disabled:opacity-30 disabled:cursor-not-allowed group shadow-xl shadow-slate-200"
                >
                  {isDistributing ? (
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Обработка...
                    </div>
                  ) : (
                    <>
                      <Play size={14} className="group-hover:translate-x-0.5 transition-transform" />
                      Создать график
                    </>
                  )}
                </button>

                <p className="text-[10px] text-slate-400 text-center font-medium">
                  {selectedDutyDays.length} дн. выбрано для распределения
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;