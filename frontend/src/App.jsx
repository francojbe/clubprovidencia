import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { UserPlus, Mail, Activity, CheckCircle2, Search, Clock, Users, Calendar, Hash, FileSpreadsheet, Edit3, Save, X, LogOut, Shield, SlidersHorizontal, Plus, Ticket } from 'lucide-react';
import ExcelJS from 'exceljs';
import { saveAs } from 'file-saver';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CLASES_OPTIONS = [
  "Acondicionamiento Físico",
  "Baile Entretenido",
  "Clases de Natación",
  "Entrenamiento Funcional",
  "Esgrima",
  "G.A.P.",
  "Gimnasio Fitness",
  "Hidrogimnasia",
  "Nado Libre",
  "Pilates",
  "Pilates Fitness",
  "Spinning",
  "Zumba",
  "Otro"
];

const normalizeClase = (rawClase) => {
  if (!rawClase) return "Sin especificar";
  const str = String(rawClase).toLowerCase().trim();
  
  if (str.includes("nado") || str.includes("nadp") || str.includes("nadolibre") || str.includes("nadi")) return "Nado Libre";
  if (str.includes("zumba") || str.includes("zumm") || str.includes("zumbe")) return "Zumba";
  if (str.includes("hidro") || str.includes("aquafit")) return "Hidrogimnasia";
  if (str.includes("esgrima")) return "Esgrima";
  if (str.includes("natacion") || str.includes("nataci")) return "Clases de Natación";
  if (str.includes("gap") || str.includes("g.a.p") || str.includes("g a p")) return "G.A.P.";
  if (str.includes("spin")) return "Spinning";
  if (str.includes("funcional")) return "Entrenamiento Funcional";
  if (str.includes("acondicionamiento")) return "Acondicionamiento Físico";
  if (str.includes("baile")) return "Baile Entretenido";
  
  if (str.includes("pilates") || str.includes("pitales") || str.includes("pilate")) {
    if (str.includes("fit") || str.includes("fines")) return "Pilates Fitness";
    return "Pilates";
  }
  
  if (str.includes("fit") || str.includes("gym") || str.includes("gimnasio") || str.includes("gimnacio") || str.includes("fines")) return "Gimnasio Fitness";

  if (str.includes("2026") || str.includes("karina")) return "Otro";
  
  return rawClase;
};

// Utility to generate a badge color based on class name
const getBadgeColor = (clase) => {
  const colors = [
    'bg-purple-50 text-purple-600', 'bg-green-50 text-green-600', 
    'bg-blue-50 text-blue-600', 'bg-orange-50 text-orange-600',
    'bg-pink-50 text-pink-600', 'bg-sky-50 text-sky-600'
  ];
  let hash = 0;
  for (let i = 0; i < clase.length; i++) hash = clase.charCodeAt(i) + ((hash << 5) - hash);
  const index = Math.abs(hash) % colors.length;
  return colors[index];
};

export default function App() {
  const [activeView, setActiveView] = useState('registro'); 
  
  return (
    <div className="flex h-screen bg-white text-slate-900 font-sans overflow-hidden selection:bg-slate-200">
      {/* Sidebar - Minimalist like Orio */}
      <aside className="w-[280px] bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
        <div className="px-6 py-8">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-slate-900 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-lg leading-none">C</span>
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-slate-900">ClubSys</h1>
          </div>
          
          <div className="relative mt-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="Buscar..." 
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-slate-300"
            />
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          <div className="space-y-0.5">
            <SidebarItem icon={<Clock />} label="Inicio" active={false} />
            <SidebarItem icon={<Shield />} label="Seguridad" active={false} />
            
            <div className="pt-4 pb-1">
              <p className="px-3 text-xs font-semibold text-slate-500 mb-2">Gestión de accesos</p>
              <SidebarItem icon={<Users />} label="Directorio" active={activeView === 'directorio'} onClick={() => setActiveView('directorio')} />
              <SidebarItem icon={<UserPlus />} label="Control Ingreso" active={activeView === 'registro'} onClick={() => setActiveView('registro')} />
              <SidebarItem icon={<FileSpreadsheet />} label="Reportes" active={activeView === 'reportes'} onClick={() => setActiveView('reportes')} />
              <SidebarItem icon={<Ticket />} label="ClassPass" active={activeView === 'classpass'} onClick={() => setActiveView('classpass')} />
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center text-slate-500 font-medium">
              CP
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">Recepción</p>
              <p className="text-xs text-slate-500">Club Providencia</p>
            </div>
          </div>
          <button className="text-slate-400 hover:text-slate-600"><LogOut size={18}/></button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto bg-white">
        <div className="max-w-[1200px] mx-auto p-10">
          <AnimatePresence mode="wait">
            {activeView === 'registro' && <motion.div key="registro" initial={{opacity:0, y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} transition={{duration: 0.2}}><RegistroView /></motion.div>}
            {activeView === 'directorio' && <motion.div key="directorio" initial={{opacity:0, y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} transition={{duration: 0.2}}><DirectorioView /></motion.div>}
            {activeView === 'reportes' && <motion.div key="reportes" initial={{opacity:0, y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} transition={{duration: 0.2}}><ReportesView /></motion.div>}
            {activeView === 'classpass' && <motion.div key="classpass" initial={{opacity:0, y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} transition={{duration: 0.2}}><ClassPassView /></motion.div>}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

function SidebarItem({ icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
        active 
        ? 'bg-slate-100 text-slate-900' 
        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
      }`}
    >
      <span className={active ? 'text-slate-900' : 'text-slate-400'}>
        {React.cloneElement(icon, { size: 18 })}
      </span>
      <span>{label}</span>
    </button>
  );
}

// ==========================================
// VIEW: REGISTRO (CHECK-IN)
// ==========================================
function RegistroView() {
  const [users, setUsers] = useState([]);
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [clase, setClase] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const wrapperRef = useRef(null);

  useEffect(() => { axios.get(`${API_BASE_URL}/users`).then(res => setUsers(res.data)); }, []);

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) setShowSuggestions(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [wrapperRef]);

  const filteredUsers = users.filter(u => u.nombre.toLowerCase().includes(nombre.toLowerCase())).slice(0, 15);

  const handleSelectUser = (user) => {
    setNombre(user.nombre);
    setEmail(user.email);
    setShowSuggestions(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!nombre || !clase) return;
    setIsLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/register`, { nombre, email, clase });
      setSuccessMsg(`Ingreso registrado para ${nombre}`);
      setNombre(''); setEmail(''); setClase('');
      axios.get(`${API_BASE_URL}/users`).then(r => setUsers(r.data));
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      alert("Error al registrar el ingreso");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <div className="mb-10">
        <h2 className="text-[32px] font-semibold text-slate-900 tracking-tight">Control de Ingreso</h2>
        <div className="flex space-x-6 mt-6 border-b border-slate-200">
          <button className="pb-3 border-b-2 border-slate-900 text-sm font-medium text-slate-900">Nueva Entrada</button>
          <button className="pb-3 text-sm font-medium text-slate-500 hover:text-slate-800">Escanear QR</button>
        </div>
      </div>

      <div className="mt-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative" ref={wrapperRef}>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Socio *</label>
            <div className="relative">
              <input type="text" value={nombre} onChange={(e) => { setNombre(e.target.value); setShowSuggestions(true); }} onFocus={() => setShowSuggestions(true)} className="w-full bg-white border border-slate-200 text-slate-900 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-slate-300 transition-shadow text-sm" placeholder="Buscar por nombre..." required autoFocus/>
            </div>
            <AnimatePresence>
              {showSuggestions && nombre && filteredUsers.length > 0 && (
                <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }} className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg overflow-hidden py-1">
                  <ul className="max-h-60 overflow-y-auto">
                    {filteredUsers.map((u, i) => (
                      <li key={i} onClick={() => handleSelectUser(u)} className="px-4 py-2 hover:bg-slate-50 cursor-pointer flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-medium text-slate-600">{u.nombre.charAt(0)}</div>
                        <div>
                          <p className="text-sm font-medium text-slate-900 leading-tight">{u.nombre}</p>
                          <p className="text-xs text-slate-500">{u.email || "Sin correo"}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Correo electrónico (Opcional)</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full bg-white border border-slate-200 text-slate-900 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-slate-300 text-sm" placeholder="ejemplo@correo.com"/>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Actividad o Clase *</label>
              <select value={clase} onChange={(e) => setClase(e.target.value)} required className="w-full bg-white border border-slate-200 text-slate-900 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-slate-300 text-sm appearance-none">
                <option value="" disabled>Seleccionar actividad...</option>
                {CLASES_OPTIONS.map((c, i) => <option key={i} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          <div className="pt-4 flex items-center space-x-3">
            <button type="submit" disabled={isLoading || !nombre || !clase} className="bg-slate-900 hover:bg-slate-800 text-white font-medium py-2 px-5 rounded-lg text-sm flex items-center justify-center transition-colors disabled:opacity-50">
              {isLoading ? <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span> : "Registrar Acceso"}
            </button>
            <button type="button" onClick={()=>{setNombre('');setEmail('');setClase('')}} className="bg-white border border-slate-200 text-slate-700 font-medium py-2 px-5 rounded-lg text-sm hover:bg-slate-50 transition-colors">
              Limpiar
            </button>
          </div>
        </form>
      </div>

      <AnimatePresence>
        {successMsg && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }} className="mt-8 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg flex items-center space-x-2">
            <CheckCircle2 size={18} className="text-green-600"/> <span className="text-sm font-medium">{successMsg}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ==========================================
// VIEW: REPORTES
// ==========================================
function ReportesView() {
  const [attendance, setAttendance] = useState([]);
  const [users, setUsers] = useState([]);
  const [displayCount, setDisplayCount] = useState(100);
  const [globalSearch, setGlobalSearch] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'fecha', direction: 'desc' });
  
  const [filters, setFilters] = useState({
    nombre: '',
    email: '',
    clase: '',
    horario: '',
    fecha: ''
  });
  
  useEffect(() => {
    axios.get(`${API_BASE_URL}/attendance`).then(res => setAttendance(res.data));
    axios.get(`${API_BASE_URL}/users`).then(res => setUsers(res.data));
  }, []);

  const userMap = users.reduce((acc, u) => {
    acc[u.id] = u;
    return acc;
  }, {});

  const enrichedAttendance = attendance.map(a => {
    let formattedDate = a.fecha ? a.fecha.split(' ')[0] : "";
    const parts = formattedDate.split('-');
    if (parts.length === 3 && parts[0].length === 4) {
      formattedDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
    return {
      ...a,
      email: userMap[a.client_id]?.email || "",
      fecha: formattedDate,
      clase: normalizeClase(a.clase)
    };
  });

  const filteredAttendance = enrichedAttendance.filter(a => {
    const matchesGlobal = globalSearch === '' || 
      Object.values(a).some(val => String(val).toLowerCase().includes(globalSearch.toLowerCase()));
      
    let matchesFecha = true;
    if (filters.fecha) {
        // filters.fecha comes as YYYY-MM-DD from type="date"
        const ddmmyyyy = filters.fecha.split('-').reverse().join('-');
        const yyyymmdd = filters.fecha;
        matchesFecha = a.fecha.includes(ddmmyyyy) || a.fecha.includes(yyyymmdd) || a.fecha.replace(/\//g, '-').includes(ddmmyyyy);
    }

    const matchesColumns = 
      a.nombre.toLowerCase().includes(filters.nombre.toLowerCase()) &&
      a.email.toLowerCase().includes(filters.email.toLowerCase()) &&
      a.clase.toLowerCase().includes(filters.clase.toLowerCase()) &&
      a.horario.toLowerCase().includes(filters.horario.toLowerCase()) &&
      matchesFecha;

    return matchesGlobal && matchesColumns;
  });

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedAndFilteredAttendance = [...filteredAttendance].sort((a, b) => {
    if (!sortConfig.key) return 0;
    let aVal = a[sortConfig.key] || "";
    let bVal = b[sortConfig.key] || "";
    
    if (sortConfig.key === 'fecha') {
      const parseDate = (d) => {
        if (!d) return 0;
        const parts = d.split('-');
        if (parts.length === 3) {
           if (parts[0].length === 4) return new Date(d).getTime(); // YYYY-MM-DD
           return new Date(`${parts[2]}-${parts[1]}-${parts[0]}`).getTime(); // DD-MM-YYYY
        }
        return 0;
      };
      aVal = parseDate(a.fecha);
      bVal = parseDate(b.fecha);
    } else {
      aVal = String(aVal).toLowerCase();
      bVal = String(bVal).toLowerCase();
    }
    
    if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const handleExportExcel = async () => {
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Reporte de Accesos');

    worksheet.mergeCells('A1', 'E1');
    const titleRow = worksheet.getCell('A1');
    titleRow.value = 'REPORTE OFICIAL DE ACCESOS - CLUB PROVIDENCIA';
    titleRow.font = { name: 'Arial', size: 14, bold: true, color: { argb: 'FFFFFFFF' } };
    titleRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF0F172A' } };
    titleRow.alignment = { vertical: 'middle', horizontal: 'center' };
    worksheet.getRow(1).height = 35;

    worksheet.mergeCells('A2', 'E2');
    const subtitleRow = worksheet.getCell('A2');
    subtitleRow.value = `Generado el: ${new Date().toLocaleDateString('es-CL')} a las ${new Date().toLocaleTimeString('es-CL')}`;
    subtitleRow.font = { name: 'Arial', size: 10, italic: true, color: { argb: 'FF475569' } };
    subtitleRow.alignment = { vertical: 'middle', horizontal: 'right' };
    worksheet.getRow(2).height = 20;

    const headersRow = worksheet.getRow(4);
    const headers = ['NOMBRE DEL SOCIO', 'CORREO ELECTRÓNICO', 'CLASE / ACTIVIDAD', 'HORARIO', 'FECHA'];
    headers.forEach((header, index) => {
      const cell = headersRow.getCell(index + 1);
      cell.value = header;
      cell.font = { name: 'Arial', size: 10, bold: true, color: { argb: 'FFFFFFFF' } };
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF334155' } };
      cell.alignment = { vertical: 'middle', horizontal: 'center' };
      cell.border = { top: {style:'thin'}, left: {style:'thin'}, bottom: {style:'thin'}, right: {style:'thin'} };
    });
    headersRow.height = 25;

    worksheet.columns = [
      { key: 'nombre', width: 35 },
      { key: 'email', width: 35 },
      { key: 'clase', width: 25 },
      { key: 'horario', width: 15 },
      { key: 'fecha', width: 15 },
    ];

    sortedAndFilteredAttendance.forEach((a, index) => {
      const row = worksheet.addRow({ nombre: a.nombre, email: a.email || "—", clase: a.clase, horario: a.horario, fecha: a.fecha });
      row.eachCell((cell, colNumber) => {
        cell.font = { name: 'Arial', size: 10, color: { argb: 'FF1E293B' } };
        cell.border = {
          top: {style:'thin', color: {argb:'FFE2E8F0'}}, left: {style:'thin', color: {argb:'FFE2E8F0'}}, 
          bottom: {style:'thin', color: {argb:'FFE2E8F0'}}, right: {style:'thin', color: {argb:'FFE2E8F0'}}
        };
        cell.alignment = colNumber > 2 ? { horizontal: 'center' } : { horizontal: 'left', indent: 1 };
        if (index % 2 === 1) cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF8FAFC' } };
      });
    });

    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(blob, `ClubProvidencia_ReporteAccesos_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  return (
    <div className="w-full">
      <div className="flex justify-between items-end mb-6">
        <h2 className="text-[32px] font-semibold text-slate-900 tracking-tight">Registro de Accesos</h2>
        
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={14} />
            <input 
              type="text" 
              placeholder="Búsqueda global..." 
              value={globalSearch}
              onChange={(e) => setGlobalSearch(e.target.value)}
              className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-slate-300" 
            />
          </div>
          <button onClick={handleExportExcel} className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors flex items-center space-x-2">
            <FileSpreadsheet size={16} />
            <span>Exportar Excel</span>
          </button>
        </div>
      </div>

      <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="px-4 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wider min-w-[200px]">
                  <div className="cursor-pointer hover:text-slate-900 flex items-center space-x-1" onClick={() => handleSort('nombre')}>
                    <span>NOMBRE</span>
                    {sortConfig.key === 'nombre' && <span className="text-[10px]">{sortConfig.direction === 'asc' ? '▼' : '▲'}</span>}
                  </div>
                  <input type="text" placeholder="Filtrar..." className="mt-1.5 w-full bg-white border border-slate-200 rounded px-2 py-1.5 text-xs font-normal normal-case focus:outline-none focus:border-slate-300" value={filters.nombre} onChange={e => setFilters({...filters, nombre: e.target.value})} />
                </th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wider min-w-[200px]">
                  <div className="cursor-pointer hover:text-slate-900 flex items-center space-x-1" onClick={() => handleSort('email')}>
                    <span>MAIL</span>
                    {sortConfig.key === 'email' && <span className="text-[10px]">{sortConfig.direction === 'asc' ? '▼' : '▲'}</span>}
                  </div>
                  <input type="text" placeholder="Filtrar..." className="mt-1.5 w-full bg-white border border-slate-200 rounded px-2 py-1.5 text-xs font-normal normal-case focus:outline-none focus:border-slate-300" value={filters.email} onChange={e => setFilters({...filters, email: e.target.value})} />
                </th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wider min-w-[150px]">
                  <div className="cursor-pointer hover:text-slate-900 flex items-center space-x-1" onClick={() => handleSort('clase')}>
                    <span>CLASE</span>
                    {sortConfig.key === 'clase' && <span className="text-[10px]">{sortConfig.direction === 'asc' ? '▼' : '▲'}</span>}
                  </div>
                  <input type="text" placeholder="Filtrar..." className="mt-1.5 w-full bg-white border border-slate-200 rounded px-2 py-1.5 text-xs font-normal normal-case focus:outline-none focus:border-slate-300" value={filters.clase} onChange={e => setFilters({...filters, clase: e.target.value})} />
                </th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wider min-w-[120px]">
                  <div className="cursor-pointer hover:text-slate-900 flex items-center space-x-1" onClick={() => handleSort('horario')}>
                    <span>HORARIO</span>
                    {sortConfig.key === 'horario' && <span className="text-[10px]">{sortConfig.direction === 'asc' ? '▼' : '▲'}</span>}
                  </div>
                  <input type="text" placeholder="Filtrar..." className="mt-1.5 w-full bg-white border border-slate-200 rounded px-2 py-1.5 text-xs font-normal normal-case focus:outline-none focus:border-slate-300" value={filters.horario} onChange={e => setFilters({...filters, horario: e.target.value})} />
                </th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wider min-w-[120px]">
                  <div className="cursor-pointer hover:text-slate-900 flex items-center space-x-1" onClick={() => handleSort('fecha')}>
                    <span>FECHA</span>
                    {sortConfig.key === 'fecha' && <span className="text-[10px]">{sortConfig.direction === 'asc' ? '▼' : '▲'}</span>}
                  </div>
                  <input type="date" className="mt-1.5 w-full bg-white border border-slate-200 rounded px-2 py-1.5 text-xs font-normal normal-case focus:outline-none focus:border-slate-300 text-slate-600" value={filters.fecha} onChange={e => setFilters({...filters, fecha: e.target.value})} />
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedAndFilteredAttendance.slice(0, displayCount).map((a, i) => (
                <tr key={i} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors group">
                  <td className="px-4 py-4">
                    <p className="text-sm font-medium text-slate-900">{a.nombre}</p>
                  </td>
                  <td className="px-4 py-4 text-sm text-slate-600">{a.email || "—"}</td>
                  <td className="px-4 py-4">
                    <span className={`px-2.5 py-1 rounded-md text-xs font-medium ${getBadgeColor(a.clase)}`}>
                      {a.clase}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm text-slate-900 font-medium">{a.horario}</td>
                  <td className="px-4 py-4 text-sm text-slate-600">{a.fecha}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {sortedAndFilteredAttendance.length === 0 && (
          <div className="p-16 text-center text-slate-500 text-sm">No se encontraron registros con esos filtros.</div>
        )}
        {sortedAndFilteredAttendance.length > displayCount && (
          <div className="p-4 flex justify-between items-center bg-slate-50 border-t border-slate-200">
            <span className="text-xs font-medium text-slate-500">Mostrando {displayCount} de {sortedAndFilteredAttendance.length} resultados</span>
            <button onClick={() => setDisplayCount(prev => prev + 100)} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors">
              Cargar más registros
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ==========================================
// VIEW: DIRECTORIO DE SOCIOS
// ==========================================
function DirectorioView() {
  const [users, setUsers] = useState([]);
  const [displayCount, setDisplayCount] = useState(50);
  const [sortOrder, setSortOrder] = useState('asc');
  
  useEffect(() => { axios.get(`${API_BASE_URL}/users`).then(res => setUsers(res.data)); }, []);

  const sortedUsers = [...users].sort((a, b) => {
    if (sortOrder === 'asc') return a.nombre.localeCompare(b.nombre);
    return b.nombre.localeCompare(a.nombre);
  });

  return (
    <div className="w-full">
      <div className="flex justify-between items-end mb-6">
        <h2 className="text-[32px] font-semibold text-slate-900 tracking-tight">Directorio de Socios</h2>
        <div className="flex items-center space-x-3">
          <button className="px-4 py-2 border border-slate-200 rounded-lg text-slate-700 text-sm font-medium hover:bg-slate-50">Editar permisos</button>
          <button className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 flex items-center">
            <Plus size={16} className="mr-1.5"/> Añadir socio
          </button>
        </div>
      </div>

      <div className="flex space-x-6 border-b border-slate-200 mb-6">
        <button className="pb-3 border-b-2 border-slate-900 text-sm font-medium text-slate-900">Socios activos</button>
        <button className="pb-3 text-sm font-medium text-slate-500 hover:text-slate-800">Grupos</button>
      </div>

      <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200">
              <th 
                className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100 transition-colors"
                onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
              >
                <div className="flex items-center space-x-1">
                  <span>Socio</span>
                  <span className="text-[10px]">{sortOrder === 'asc' ? '▼' : '▲'}</span>
                </div>
              </th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Contacto</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Estado</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider w-10"></th>
            </tr>
          </thead>
          <tbody>
            {sortedUsers.slice(0, displayCount).map((u, i) => (
              <tr key={i} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors group">
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-medium text-slate-600">
                      {u.nombre.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{u.nombre}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-slate-900">{u.email || "—"}</p>
                  <p className="text-xs text-slate-500">{u.telefono || "—"}</p>
                </td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-green-50 text-green-600">Activo</span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button className="text-slate-400 hover:text-slate-700 opacity-0 group-hover:opacity-100"><Edit3 size={16}/></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length > displayCount && (
          <div className="p-4 flex justify-center bg-slate-50 border-t border-slate-200">
            <button onClick={() => setDisplayCount(prev => prev + 50)} className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-100 transition-colors">
              Cargar más socios
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ==========================================
// VIEW: CLASSPASS
// ==========================================
function ClassPassView() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchTime, setSearchTime] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [searchDuration, setSearchDuration] = useState(null);
  const [source, setSource] = useState('');
  const [status, setStatus] = useState({ last_sync: null, is_fresh: false });

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/classpass/status`);
      setStatus(res.data);
    } catch (e) {
      console.error("Error al obtener estado del caché:", e);
    }
  };

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/api/classpass/sync`);
      alert(res.data.message);
      await fetchStatus();
    } catch (err) {
      alert("Error al sincronizar clases de ClassPass. Revisa que el backend esté encendido.");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery) return;
    setIsLoading(true);
    setSearchResults(null);
    setSearchDuration(null);
    setSource('');
    const startTime = performance.now();
    try {
      let url = `${API_BASE_URL}/api/classpass/search?q=${encodeURIComponent(searchQuery)}`;
      if (searchTime) {
        url += `&time=${encodeURIComponent(searchTime)}`;
      }
      const response = await axios.get(url);
      const endTime = performance.now();
      setSearchDuration(((endTime - startTime) / 1000).toFixed(2));
      setSearchResults(response.data.data);
      setSource(response.data.source || 'live');
      await fetchStatus(); // Recargar status por si actualizó el caché
    } catch (err) {
      alert("Error al ejecutar la búsqueda de ClassPass");
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-[32px] font-semibold text-slate-900 tracking-tight">Integración ClassPass (RPA + DB)</h2>
        <p className="text-slate-500 mt-2">
          Busca alumnos registrados hoy en la base de datos local o haz una consulta en vivo a ClassPass a través del bot.
        </p>
      </div>

      {/* Tarjeta de Estado del Caché y Sincronización Masiva */}
      <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between bg-slate-50 border border-slate-200 rounded-xl p-5 gap-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <span>Base de Datos de Reservas</span>
            <span className={`inline-block w-2.5 h-2.5 rounded-full ${status.is_fresh ? 'bg-green-500 animate-pulse' : 'bg-amber-500'}`}></span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            {status.last_sync 
              ? `Último barrido masivo: ${new Date(status.last_sync).toLocaleTimeString()} (${status.is_fresh ? 'Caché activo < 15 min' : 'Expirado, búsquedas caerán en vivo'})` 
              : "No se ha realizado un barrido masivo hoy."}
          </p>
        </div>
        
        <button 
          onClick={handleSync}
          disabled={isSyncing || isLoading}
          className="bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 transition-all shadow-sm"
        >
          {isSyncing ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              <span>Mapeando Clases del Día (1-2 min)...</span>
            </>
          ) : (
            <>
              <span>⚡ Mapear Todo el Día (Búsquedas Instantáneas)</span>
            </>
          )}
        </button>
      </div>

      <div className="flex space-x-3 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Buscar persona por nombre o correo..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full bg-white border border-slate-200 text-slate-900 rounded-xl pl-12 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent shadow-sm transition-shadow text-base" 
          />
        </div>
        <div className="relative w-36">
          <Clock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="time" 
            value={searchTime}
            onChange={(e) => setSearchTime(e.target.value)}
            className="w-full bg-white border border-slate-200 text-slate-900 rounded-xl pl-10 pr-3 py-3.5 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent shadow-sm transition-shadow text-base cursor-text" 
            title="Filtrar por hora (Opcional)"
          />
        </div>
        <button 
          onClick={handleSearch} 
          disabled={isLoading || !searchQuery || isSyncing}
          className="bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white px-6 rounded-xl font-medium flex items-center justify-center min-w-[150px] transition-colors"
        >
          {isLoading ? (
            <span className="flex items-center space-x-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              <span>Buscando...</span>
            </span>
          ) : (
            "Buscar"
          )}
        </button>
      </div>

      <div className="space-y-4">
        {isLoading && (
          <div className="p-12 text-center border border-dashed border-slate-300 rounded-xl bg-slate-50">
             <div className="w-10 h-10 border-4 border-slate-300 border-t-slate-900 rounded-full animate-spin mx-auto mb-4"></div>
             <p className="text-slate-900 font-semibold mb-1">Buscando asistente...</p>
             <p className="text-slate-500 text-sm">Si el caché está expirado, el bot se conectará a ClassPass. Esto tomará unos 25 segundos.</p>
          </div>
        )}

        {!isLoading && searchResults === null && (
           <div className="p-12 text-center border border-dashed border-slate-300 rounded-xl bg-slate-50">
             <Ticket className="mx-auto text-slate-300 mb-3" size={32} />
             <p className="text-slate-500 font-medium text-sm">Ingresa un nombre para buscar reservas activas.</p>
           </div>
        )}

        {!isLoading && searchResults !== null && searchResults.length === 0 && (
           <div className="p-12 text-center border border-dashed border-slate-300 rounded-xl bg-slate-50">
             <p className="text-slate-500 text-sm">No se encontraron reservas hoy en ClassPass para "{searchQuery}".</p>
           </div>
        )}

        {!isLoading && searchResults !== null && searchResults.length > 0 && (
          <>
            {searchResults.map(user => (
              <div key={user.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">{user.nombre}</h3>
                    <p className="text-sm text-slate-500">{user.email || "Sin correo electrónico"}</p>
                  </div>
                  <div className="text-right flex flex-col items-end gap-1.5">
                    <span className={`inline-block text-xs font-semibold px-2.5 py-1 rounded-full ${source === 'cache' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                      {source === 'cache' ? '⚡ Caché de Base de Datos' : '🤖 Búsqueda en Vivo (RPA)'}
                    </span>
                    <span className="inline-block bg-slate-100 text-slate-700 text-xs font-semibold px-2.5 py-1 rounded-full">
                      {user.classes.length} clases hoy
                    </span>
                  </div>
                </div>
                
                {user.classes.length > 0 ? (
                  <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {user.classes.map((cls, idx) => (
                      <div key={idx} className="flex items-center space-x-3 bg-slate-50 border border-slate-100 p-3 rounded-lg">
                        <div className="bg-white border border-slate-200 p-2 rounded-md shadow-sm">
                          <Calendar size={16} className="text-slate-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-900">{cls.clase}</p>
                          <p className="text-xs text-slate-500">{cls.fecha} • {cls.horario}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-4 text-sm text-slate-500 italic bg-slate-50 p-3 rounded-lg text-center">
                    Este usuario no tiene clases agendadas.
                  </div>
                )}
              </div>
            ))}
            {searchDuration && (
              <p className="text-right text-xs font-medium text-slate-400 mt-2 mr-2">
                ⏱️ Consulta completada en {searchDuration} segundos ({source === 'cache' ? 'instantáneo desde DB' : 'raspado en vivo'})
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
