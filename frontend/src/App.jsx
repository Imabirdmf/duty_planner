import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Calendar, Users, Play, X, Info, ClipboardList,
  Plus, AlertCircle, Save, ChevronRight, UserMinus, Trash2
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

  // Состояние для выпадающего календаря добавления выходного (popover)
  const [activePopover, setActivePopover] = useState(null);

  // --- Эффекты ---

  // Таймер для автоматического скрытия ошибок (5 секунд)
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // --- Вспомогательные функции ---

  // Обновленный трансформер под структуру { data: [...], errors: {...} }
  const transformDuties = (response) => {
    const items = response.data;
    if (!items || !Array.isArray(items)) return null;

    return items.reduce((acc, item) => {
      acc[item.date] = item.users.map(u => ({
        id: u.id,
        name: u.full_name // Для карточек результата оставляем full_name как более информативное
      }));
      return acc;
    }, {});
  };

  // --- API запросы ---

  const fetchInitialData = async () => {
    setIsLoadingUsers(true);
    setError(null);
    try {
      const [usersRes, vacationsRes] = await Promise.all([
        api.get('/api/users/'),
        api.get('/api/days-off/')
      ]);
      setUsers(usersRes.data);
      setVacations(vacationsRes.data);
    } catch (err) {
      console.error(err);
      setError("Ошибка связи с сервером. Убедитесь, что Django запущен на порту 8000.");
    } finally {
      setIsLoadingUsers(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleAddVacation = async (userId, date) => {
    if (!date || !userId) return;
    setError(null);

    try {
      const res = await api.post('/api/days-off/', {
        user: userId,
        date: date
      });
      setVacations(prev => [...prev, res.data]);
      setActivePopover(null);
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data) {
        const data = err.response.data;
        let errorMessage = "Не удалось добавить выходной день.";
        if (data.non_field_errors) {
          errorMessage = data.non_field_errors.join(", ");
        } else if (data.date) {
          errorMessage = Array.isArray(data.date) ? data.date.join(", ") : data.date;
        } else if (data.detail) {
          errorMessage = data.detail;
        }
        setError(errorMessage);
      } else {
        setError("Сетевая ошибка при попытке добавить выходной.");
      }
    }
  };

  const handleDeleteVacation = async (id) => {
    try {
      await api.delete(`/api/days-off/${id}/`);
      setVacations(prev => prev.filter(v => v.id !== id));
    } catch (err) {
      setError("Ошибка при удалении записи.");
    }
  };

  const handleGenerate = async () => {
    setIsDistributing(true);
    setError(null);
    try {
      const res = await api.post('/api/duties/generate/', {
        month: currentMonth,
        people_per_day: parseInt(shiftSize),
        dates: selectedDutyDays
      });
      setTimetable(transformDuties(res.data));
    } catch (err) {
      console.error(err);
      setError("Ошибка алгоритма генерации. Проверьте параметры и доступность сотрудников.");
    } finally {
      setIsDistributing(false);
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
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl flex items-center justify-between animate-in fade-in zoom-in slide-in-from-top-4 sticky top-4 z-50 shadow-lg transition-all duration-300">
            <div className="flex items-center gap-2 font-medium">
              <AlertCircle size={18} />
              {error}
            </div>
            <button onClick={() => setError(null)} className="p-1 hover:bg-red-100 rounded-lg transition-colors">
              <X size={18} />
            </button>
          </div>
        )}

        <header className="flex flex-col md:flex-row justify-between items-center bg-white p-6 rounded-3xl shadow-sm border border-slate-100 gap-4">
          <div>
            <h1 className="text-2xl font-black text-slate-800 tracking-tight">Duty<span className="text-blue-600">Planner</span></h1>
            <p className="text-slate-400 text-sm font-medium">Управление расписанием через API</p>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          <div className="lg:col-span-8 space-y-6">
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
              <div className="p-5 border-b border-slate-50 flex items-center gap-2 font-bold text-slate-700">
                <Users size={18} className="text-blue-600" />
                Команда и доступность
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-slate-50/50">
                    <tr className="text-[10px] uppercase font-black text-slate-400">
                      <th className="px-6 py-4 w-1/3">Сотрудник</th>
                      <th className="px-6 py-4">Выходные / Отпуска</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {isLoadingUsers ? (
                      [1,2,3].map(i => (
                        <tr key={i} className="animate-pulse">
                          <td className="px-6 py-4"><div className="h-4 bg-slate-100 rounded w-24"></div></td>
                          <td className="px-6 py-4"><div className="h-4 bg-slate-100 rounded w-full"></div></td>
                        </tr>
                      ))
                    ) : (
                      users.map(u => (
                        <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4">
                            {/* Возвращено использование u.name */}
                            <div className="font-bold text-slate-800">{u.full_name}</div>
                            <div className="text-[11px] text-slate-400">{u.email}</div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex flex-wrap gap-2 items-center relative">
                              {vacations
                                .filter(v => v.user === u.id)
                                .map(v => (
                                  <div key={v.id} className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 border border-blue-100 rounded-xl text-[10px] font-bold text-blue-600 shadow-sm group animate-in fade-in scale-in">
                                    {v.date}
                                    <button
                                      onClick={() => handleDeleteVacation(v.id)}
                                      className="hover:text-red-500 transition-colors ml-1"
                                    >
                                      <X size={12} strokeWidth={3} />
                                    </button>
                                  </div>
                                ))}

                              <div className="relative">
                                <button
                                  onClick={() => setActivePopover(activePopover === u.id ? null : u.id)}
                                  className={`p-1.5 border rounded-xl transition-all ${activePopover === u.id ? 'bg-blue-600 border-blue-600 text-white' : 'border-dashed border-slate-200 text-slate-400 hover:border-blue-400 hover:text-blue-500 hover:bg-blue-50'}`}
                                >
                                  {activePopover === u.id ? <X size={14} /> : <Plus size={14} />}
                                </button>

                                {activePopover === u.id && (
                                  <div className="absolute left-0 top-full mt-2 z-20 bg-white border border-slate-100 shadow-xl rounded-2xl p-3 animate-in fade-in slide-in-from-top-1 w-48">
                                    <label className="text-[9px] font-black text-slate-400 uppercase mb-2 block">Выбрать дату:</label>
                                    <input
                                      type="date"
                                      autoFocus
                                      className="w-full text-xs font-bold p-2 bg-slate-50 border-0 rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                                      onChange={(e) => handleAddVacation(u.id, e.target.value)}
                                    />
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
              <div className="flex items-center gap-2 font-bold text-slate-700 mb-6">
                <ClipboardList size={18} className="text-blue-600" />
                Результат планирования
              </div>
              {!timetable ? (
                <div className="py-20 text-center border-2 border-dashed border-slate-100 rounded-[2rem] bg-slate-50/30">
                  <Info className="mx-auto text-slate-200 mb-2" size={40} />
                  <p className="text-slate-400 text-sm font-medium">Нет данных для отображения</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {Object.entries(timetable).sort().map(([date, assignedUsers]) => (
                    <div key={date} className="p-4 bg-white border border-slate-100 rounded-2xl shadow-sm">
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-[10px] font-black text-blue-600 uppercase tracking-widest">{new Date(date).toLocaleDateString('ru-RU', {weekday:'short'})}</span>
                        <span className="text-xs font-black text-slate-700">{date}</span>
                      </div>
                      <div className="space-y-2">
                        {assignedUsers.map(u => (
                          <div key={u.id} className="bg-slate-50 p-2 rounded-lg text-[11px] font-bold text-slate-600">
                            {u.name}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-4 space-y-6">
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 sticky top-8">
              <div className="flex items-center gap-2 font-bold text-slate-700 border-b border-slate-50 pb-4 mb-6">
                <Calendar size={18} className="text-blue-600" />
                Параметры
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Период</label>
                  <input type="month" value={currentMonth} onChange={e => setCurrentMonth(e.target.value)} className="w-full bg-slate-50 border-0 p-3 text-sm rounded-2xl font-bold outline-none" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Смена</label>
                  <input type="number" value={shiftSize} onChange={e => setShiftSize(e.target.value)} className="w-full bg-slate-50 border-0 p-3 text-sm rounded-2xl font-bold outline-none" />
                </div>
              </div>

              <div className="mb-8">
                <label className="text-[10px] font-black text-slate-400 uppercase mb-3 block">Выбор дат:</label>
                <div className="grid grid-cols-7 gap-1">
                  {[...Array(31)].map((_, i) => {
                    const day = i + 1;
                    const ds = `${currentMonth}-${day.toString().padStart(2, '0')}`;
                    const isSel = selectedDutyDays.includes(ds);
                    return (
                      <button
                        key={day}
                        onClick={() => toggleDaySelection(ds)}
                        className={`h-8 w-8 rounded-lg text-[10px] font-bold border transition-all ${isSel ? 'bg-blue-600 border-blue-600 text-white shadow-md' : 'bg-white border-slate-100 text-slate-300'}`}
                      >
                        {day}
                      </button>
                    );
                  })}
                </div>
              </div>

              <button
                onClick={handleGenerate}
                disabled={isDistributing || selectedDutyDays.length === 0}
                className="w-full py-4 bg-slate-900 text-white rounded-2xl font-black text-[11px] uppercase tracking-widest hover:bg-black transition-all disabled:opacity-50 flex items-center justify-center gap-3"
              >
                {isDistributing ? <div className="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full" /> : <><Play size={14} fill="currentColor" /> Генерировать</>}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;