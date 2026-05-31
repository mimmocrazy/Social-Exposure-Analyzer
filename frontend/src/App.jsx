import React, { useState, useEffect } from 'react';
import { useQuery, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, Text, Metric, Flex, ProgressBar, Title, BarChart, TextInput, Button } from '@tremor/react';
import { startAnalysis, getAnalysisStatus, login, register } from './api';

const queryClient = new QueryClient();

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error("React Crash:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 bg-red-900 text-white rounded-xl max-w-2xl mx-auto mt-12 overflow-auto">
          <h2 className="text-2xl font-bold mb-4">💥 Errore di Rendering!</h2>
          <pre className="text-xs whitespace-pre-wrap">{this.state.error && this.state.error.toString()}</pre>
          <pre className="text-xs whitespace-pre-wrap mt-4 text-red-200">{this.state.errorInfo && this.state.errorInfo.componentStack}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

// Custom Radial Progress Component
const RadialProgress = ({ score, isCritical }) => {
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const color = isCritical ? '#ef4444' : '#3b82f6'; // red-500 or blue-500

  return (
    <div className="relative flex items-center justify-center">
      <svg className="transform -rotate-90 w-40 h-40">
        <circle
          cx="80"
          cy="80"
          r={radius}
          stroke="currentColor"
          strokeWidth="12"
          fill="transparent"
          className="text-gray-800"
        />
        <motion.circle
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          cx="80"
          cy="80"
          r={radius}
          stroke={color}
          strokeWidth="12"
          fill="transparent"
          strokeDasharray={circumference}
          strokeLinecap="round"
          className="drop-shadow-lg"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center text-white">
        <span className="text-4xl font-extrabold">{score}</span>
        <span className="text-xs text-gray-400 uppercase tracking-widest mt-1">Score</span>
      </div>
    </div>
  );
};

// Icons (mock using SVG for pure independence if heroicons fails, but we assume it's installed)
const getIconForPII = (label) => {
  const l = (label || '').toLowerCase();
  if (l.includes('email')) return (
    <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
  );
  if (l.includes('phone') || l.includes('telefono')) return (
    <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
  );
  if (l.includes('location') || l.includes('indirizzo') || l.includes('place') || l.includes('luogo')) return (
    <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.243-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
  );
  if (l.includes('ip') || l.includes('server')) return (
    <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>
  );
  if (l.includes('person') || l.includes('gente') || l.includes('nome')) return (
    <svg className="w-5 h-5 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
  );
  if (l.includes('org') || l.includes('aziend') || l.includes('studio') || l.includes('societ')) return (
    <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
  );
  if (l.includes('birth') || l.includes('nascita') || l.includes('dat')) return (
    <svg className="w-5 h-5 text-pink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
  );
  if (l.includes('age') || l.includes('età') || l.includes('anni')) return (
    <svg className="w-5 h-5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
  );
  if (l.includes('occupat') || l.includes('lavor') || l.includes('profession') || l.includes('ruol') || l.includes('influenc') || l.includes('creator')) return (
    <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
  );
  if (l.includes('handle') || l.includes('username') || l.includes('social') || l.includes('profilo')) return (
    <svg className="w-5 h-5 text-pink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.206" /></svg>
  );
  // Default icon
  return (
    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
  );
};

const InteractiveLoading = () => {
  const steps = [
    { text: "Inizializzazione Deep OSINT Engine...", icon: "⚙️", delay: 0 },
    { text: "Ricerca target su Instagram...", icon: "📸", delay: 1500 },
    { text: "Analisi footprint su X (Twitter)...", icon: "🐦", delay: 3500 },
    { text: "Scansione esposizione su Facebook...", icon: "👥", delay: 5500 },
    { text: "Verifica profilo LinkedIn...", icon: "💼", delay: 7500 },
    { text: "Estrazione dati sensibili in corso...", icon: "🕵️", delay: 10000 },
    { text: "Elaborazione Audit AI tramite Gemini...", icon: "🧠", delay: 12500 },
    { text: "Finalizzazione Risk Report...", icon: "📄", delay: 16000 }
  ];

  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timers = steps.map((step, index) => 
      setTimeout(() => {
        setCurrentStep(index);
      }, step.delay)
    );
    return () => timers.forEach(t => clearTimeout(t));
  }, []);

  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center p-10 glassmorphism rounded-3xl mt-8 shadow-2xl w-full max-w-xl mx-auto border-white/5 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 animate-pulse rounded-3xl -z-10"></div>
        
        <div className="relative w-20 h-20 mb-8">
          <div className="absolute inset-0 rounded-full border-4 border-white/10"></div>
          <div className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
          <div className="absolute inset-2 rounded-full border-4 border-purple-500 border-b-transparent animate-[spin_1.5s_linear_infinite_reverse]"></div>
          
          <div className="absolute inset-0 flex items-center justify-center text-2xl">
             {steps[currentStep]?.icon || "⏳"}
          </div>
        </div>
        
        <h2 className="text-white text-2xl font-bold tracking-tight mb-6">Analisi in corso</h2>
        
        <div className="w-full flex flex-col space-y-3 relative">
          {steps.map((step, index) => {
            const isActive = index === currentStep;
            const isPast = index < currentStep;
            const isFuture = index > currentStep;
            
            if (isFuture && index > currentStep + 1) return null;
            
            return (
              <motion.div 
                key={index} 
                initial={{ opacity: 0, x: -10 }} 
                animate={{ opacity: isFuture ? 0.3 : 1, x: 0 }}
                className={`flex items-center space-x-3 p-3 rounded-xl border transition-all duration-500 ${isActive ? 'bg-blue-500/10 border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]' : isPast ? 'bg-green-500/5 border-green-500/10' : 'bg-transparent border-transparent'}`}
              >
                <div className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${isPast ? 'bg-green-500 text-white' : isActive ? 'bg-blue-500 text-white animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.6)]' : 'bg-white/10 text-gray-500'}`}>
                  {isPast ? "✓" : isActive ? "..." : ""}
                </div>
                <span className={`text-sm font-medium ${isPast ? 'text-gray-400 line-through' : isActive ? 'text-blue-400' : 'text-gray-600'}`}>
                   {step.text}
                </span>
              </motion.div>
            )
          })}
        </div>
    </motion.div>
  );
};

const OsintTelemetry = ({ rawDataDump }) => {
  if (!rawDataDump) return null;

  const scrapers = rawDataDump.scraper_results || [];
  const holehe = rawDataDump.holehe_results || [];

  return (
    <div className="w-full glassmorphism rounded-3xl p-8 mt-8 border border-white/10">
      <div className="flex items-center space-x-3 mb-6 border-b border-white/5 pb-4">
        <div className="p-2 bg-gradient-to-br from-teal-500/20 to-emerald-500/20 rounded-xl border border-white/10">
          <svg className="w-5 h-5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
        </div>
        <div>
          <h3 className="text-white text-lg font-bold tracking-tight">Telemetria Sensori OSINT</h3>
          <p className="text-gray-400 text-xs uppercase tracking-wider font-semibold">Log esecuzione moduli</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scrapers.map((s, idx) => (
          <div key={idx} className="bg-white/5 border border-white/10 p-4 rounded-2xl flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-gray-300 uppercase tracking-widest">{s.source || "Web Scraper"}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${s.status === 'ACCESSIBLE' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'}`}>
                  {s.status}
                </span>
              </div>
              <p className="text-xs text-gray-400 truncate w-full" title={s.url}>{s.url}</p>
            </div>
            {s.error && <p className="mt-3 text-xs text-red-400 bg-red-500/10 p-2 rounded-lg border border-red-500/20 font-mono">{s.error}</p>}
            {s.bio && !s.error && <p className="mt-3 text-[10px] text-gray-500 font-mono line-clamp-3 bg-black/30 p-2 rounded-lg">{s.bio}</p>}
          </div>
        ))}
        {holehe.map((h, idx) => (
          <div key={`h-${idx}`} className="bg-white/5 border border-white/10 p-4 rounded-2xl flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-gray-300 uppercase tracking-widest">Holehe (Cross-Check)</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${h.registered_sites.length > 0 ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'}`}>
                  {h.registered_sites.length} SITI
                </span>
              </div>
              <p className="text-xs text-gray-400 font-mono">{h.email}</p>
            </div>
            <div className="mt-3 flex flex-wrap gap-1">
              {h.registered_sites.map(site => (
                <span key={site} className="text-[10px] bg-red-500/10 text-red-300 px-1.5 py-0.5 rounded border border-red-500/20">
                  {site}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

function Dashboard({ analysisId }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => getAnalysisStatus(analysisId),
    refetchInterval: (data) => {
      if (!data) return 3000;
      return data.status === 'PENDING' ? 3000 : false;
    },
  });

  if (isLoading || (data && data.status === 'PENDING')) {
    return <InteractiveLoading />;
  }

  if (isError || data?.status === 'FAILED') {
    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="p-8 bg-red-950/40 border border-red-500/30 rounded-3xl mt-8 text-center max-w-lg mx-auto backdrop-blur-xl">
         <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
           <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
         </div>
         <h2 className="text-red-400 text-2xl font-bold mb-2">Analisi Fallita</h2>
         <p className="text-red-200/70">{data?.error_message || "Si è verificato un errore durante la scansione OSINT."}</p>
      </motion.div>
    );
  }

  if (data?.status === 'COMPLETED') {
    const score = data.risk_score || 0;
    const isCritical = data.risk_level === 'CRITICAL' || data.risk_level === 'HIGH';
    const isInsufficient = data.llm_report?.insufficient_data === true;

    // Pannello Profilo Privato / Dati Insufficienti
    if (isInsufficient) {
      return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-12 w-full max-w-3xl mx-auto space-y-6">
          <div className="glassmorphism rounded-3xl p-10 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-cyan-500/5 -z-10"></div>
            
            <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-emerald-500/20">
              <svg className="w-10 h-10 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            
            <h2 className="text-white text-2xl font-bold tracking-tight mb-3">Profilo Protetto</h2>
            <p className="text-gray-400 max-w-lg mx-auto leading-relaxed mb-6">
              Il profilo analizzato risulta <strong className="text-emerald-400">privato o inaccessibile</strong>. 
              Non è stato possibile estrarre dati personali esposti pubblicamente. 
              Le impostazioni di privacy dell'utente sono adeguate e limitano l'esposizione a rischi di social engineering.
            </p>
            
            <div className="inline-flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-5 py-2.5 rounded-full text-sm font-bold tracking-wider">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>RISCHIO: {data.risk_level || 'LOW'} — Score: {score}/100</span>
            </div>
          </div>

          {/* Mostra comunque il report AI se presente */}
          {data.llm_report?.mitigation_advice && (
            <div className="glassmorphism rounded-3xl p-8 border border-white/5">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl border border-white/10">
                  <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                </div>
                <h3 className="text-white text-lg font-bold">Valutazione AI</h3>
              </div>
              <p className="text-gray-300 font-light leading-relaxed">{data.llm_report.mitigation_advice}</p>
            </div>
          )}
        </motion.div>
      );
    }

    // Raggruppamento PII per evitare disordine visivo
    const labelMapping = {
      'PERSON': 'Persone Coinvolte',
      'EMAIL': 'Indirizzi Email',
      'PHONE': 'Numeri di Telefono',
      'LOCATION': 'Luoghi e Indirizzi',
      'ORGANIZATION': 'Organizzazioni / Aziende',
      'DATE_OF_BIRTH': 'Data di Nascita',
      'PLACE_OF_BIRTH': 'Luogo di Nascita',
      'AGE': 'Età Rilevata',
      'OCCUPATION': 'Ruoli e Occupazioni',
      'IP': 'Indirizzi IP',
      'SOCIAL_MEDIA_HANDLE': 'Account Social',
      'USERNAME': 'Account Social',
      'HANDLE': 'Account Social',
    };

    const piiGroups = {};
    if (data.pii_extracted && Array.isArray(data.pii_extracted)) {
      data.pii_extracted.forEach((pii) => {
        if (!pii || !pii.label) return;
        const labelKey = pii.label.toUpperCase();
        if (!piiGroups[labelKey]) {
          piiGroups[labelKey] = [];
        }
        if (pii.value && !piiGroups[labelKey].includes(pii.value)) {
          piiGroups[labelKey].push(pii.value);
        }
      });
    }

    return (
      <div className="mt-12 space-y-8 w-full max-w-7xl mx-auto text-left">
        
        {/* Top Row: Score & Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1 glassmorphism rounded-3xl p-8 flex flex-col relative overflow-hidden group">
            <div className={`absolute -inset-2 bg-gradient-to-tr ${isCritical ? 'from-red-500/20 to-orange-500/5' : 'from-blue-500/20 to-cyan-500/5'} blur-2xl -z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-700`}></div>
            <h3 className="text-gray-400 text-sm font-bold uppercase tracking-widest mb-6 text-center">Indice di Rischio</h3>
            <div className="flex justify-center mb-6">
              <RadialProgress score={score} isCritical={isCritical} />
            </div>
            
            {data.llm_report?.score_breakdown && (
              <div className="w-full mt-2 mb-4 bg-black/20 rounded-xl p-4 border border-white/5 overflow-y-auto max-h-40 custom-scrollbar">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Score Breakdown</h4>
                <div className="space-y-2">
                  {data.llm_report.score_breakdown.map((sb, idx) => (
                    <div key={idx} className="flex justify-between items-start text-xs">
                      <span className="text-gray-300 mr-2 leading-relaxed">{sb.reason}</span>
                      <span className="text-white font-bold whitespace-nowrap px-1.5 py-0.5 bg-white/10 rounded">+{sb.points_added}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="w-full space-y-4 mt-2 border-t border-white/5 pt-4">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-300 font-medium">Identità e Contatti</span>
                  <span className="text-white font-bold">{data.llm_report?.sub_scores?.identity_exposure || 0}%</span>
                </div>
                <ProgressBar value={data.llm_report?.sub_scores?.identity_exposure || 0} color="rose" className="h-1.5" />
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-300 font-medium">Network e Relazioni</span>
                  <span className="text-white font-bold">{data.llm_report?.sub_scores?.network_exposure || 0}%</span>
                </div>
                <ProgressBar value={data.llm_report?.sub_scores?.network_exposure || 0} color="orange" className="h-1.5" />
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-300 font-medium">Routine e Luoghi</span>
                  <span className="text-white font-bold">{data.llm_report?.sub_scores?.routine_exposure || 0}%</span>
                </div>
                <ProgressBar value={data.llm_report?.sub_scores?.routine_exposure || 0} color="amber" className="h-1.5" />
              </div>
            </div>

            <div className={`mt-6 px-6 py-2 mx-auto rounded-full text-sm font-extrabold tracking-widest shadow-lg border ${isCritical ? 'bg-red-500/10 text-red-400 border-red-500/20 shadow-red-500/10' : 'bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-blue-500/10'}`}>
              {data.risk_level}
            </div>
          </div>

          {/* PII Grid Widget */}
          <div className="md:col-span-2 glassmorphism rounded-3xl p-8 flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-white text-xl font-bold tracking-tight">Dati Sensibili (PII)</h3>
              <span className="text-xs bg-white/10 text-gray-300 px-3 py-1 rounded-full font-medium">{data.pii_extracted?.length || 0} Trovati</span>
            </div>
            
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 min-h-[200px]">
              {(Object.keys(piiGroups).length === 0) ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-3">
                  <svg className="w-12 h-12 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                  <p className="text-sm font-medium">Nessun dato critico esposto.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {Object.entries(piiGroups).map(([label, values], idx) => (
                    <motion.div 
                      key={label} 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="flex flex-col p-5 rounded-2xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 transition-colors group animate-fade-in"
                    >
                      <div className="flex items-center space-x-3 mb-3 pb-2 border-b border-white/5">
                        <div className="p-2 bg-white/5 rounded-xl group-hover:scale-110 transition-transform">
                          {getIconForPII(label)}
                        </div>
                        <div>
                          <p className="text-gray-400 text-[10px] font-bold uppercase tracking-wider">{label}</p>
                          <h4 className="text-white text-sm font-semibold tracking-tight">
                            {labelMapping[label] || label}
                          </h4>
                        </div>
                      </div>
                      
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {values.map((val, valIdx) => (
                          <span 
                            key={valIdx} 
                            className="bg-white/5 hover:bg-white/10 text-gray-200 text-xs px-2.5 py-1 rounded-lg transition-colors border border-white/5 break-all font-mono"
                            title={val}
                          >
                            {val}
                          </span>
                        ))}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Telemetry Section */}
        {data.raw_data_dump && <OsintTelemetry rawDataDump={data.raw_data_dump} />}

        {/* AI Audit Alert Box */}
        {data.llm_report && (
          <div className="relative overflow-hidden rounded-3xl border border-white/10 glassmorphism p-0 flex flex-col md:flex-row">
             <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-blue-500 to-purple-500 hidden md:block"></div>
             <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 to-purple-500 md:hidden"></div>
             
             {/* Left Column: Title & Threats */}
             <div className="p-8 md:w-1/3 bg-black/20 border-b md:border-b-0 md:border-r border-white/5">
                 <div className="flex items-center space-x-3 mb-6">
                   <div className="p-2.5 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl border border-white/10">
                     <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                   </div>
                   <div>
                     <h3 className="text-white text-lg font-bold tracking-tight">Audit AI</h3>
                     <p className="text-gray-400 text-xs uppercase tracking-wider font-semibold">Gemini Pro</p>
                   </div>
                 </div>

                 {data.llm_report.threat_vectors && data.llm_report.threat_vectors.length > 0 && (
                   <div>
                     <p className="text-xs text-gray-500 uppercase tracking-widest font-bold mb-3">Vettori di Minaccia Rilevati</p>
                     <div className="flex flex-wrap gap-2">
                       {data.llm_report.threat_vectors.map((threat, idx) => (
                         <span key={idx} className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20 shadow-sm">
                           <svg className="w-3 h-3 mr-1.5 opacity-70" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                           {threat}
                         </span>
                       ))}
                     </div>
                   </div>
                 )}
                 {(!data.llm_report.threat_vectors || data.llm_report.threat_vectors.length === 0) && (
                    <div className="flex items-center space-x-2 text-green-400/80 bg-green-500/5 border border-green-500/10 p-3 rounded-xl">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      <span className="text-sm font-medium">Nessuna minaccia diretta</span>
                    </div>
                 )}
             </div>

             {/* Right Column: Mitigation Advice & Sections */}
             <div className="p-8 md:w-2/3 flex flex-col justify-start overflow-y-auto max-h-[550px] custom-scrollbar">
                  <div className="flex items-center space-x-2 mb-6 border-b border-white/5 pb-4">
                     <svg className="w-5 h-5 text-blue-400 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                     <h4 className="text-blue-300 text-sm font-bold tracking-wide uppercase">Piano di Mitigazione</h4>
                  </div>
                  
                  {data.llm_report.mitigation_sections && data.llm_report.mitigation_sections.length > 0 ? (
                    <div className="space-y-6">
                      {data.llm_report.mitigation_sections.map((section, idx) => {
                        const crit = (section.criticality || '').toUpperCase();
                        const isSecCritical = crit === 'CRITICA' || crit === 'ALTA' || crit === 'HIGH' || crit === 'CRITICAL';
                        const isSecMedium = crit === 'MEDIA' || crit === 'MEDIUM';
                        
                        const badgeColor = isSecCritical 
                          ? 'bg-red-500/10 text-red-400 border-red-500/20 shadow-red-500/5' 
                          : isSecMedium 
                            ? 'bg-orange-500/10 text-orange-400 border-orange-500/20 shadow-orange-500/5' 
                            : 'bg-green-500/10 text-green-400 border-green-500/20 shadow-green-500/5';

                        return (
                          <motion.div 
                            key={idx}
                            initial={{ opacity: 0, y: 15 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 space-y-4 hover:border-white/10 transition-colors"
                          >
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-3">
                              <h5 className="text-white text-base font-bold tracking-tight">{section.title}</h5>
                              <span className={`px-3 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-widest border self-start sm:self-auto shadow-sm ${badgeColor}`}>
                                {section.criticality || 'MEDIA'}
                              </span>
                            </div>

                            <div className="space-y-4 text-sm">
                              {section.exposed_data && (
                                <div className="bg-white/[0.01] border border-white/5 rounded-xl p-4">
                                  <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest block mb-1.5">Dato Esposto Rilevato</span>
                                  <p className="text-gray-300 font-medium italic break-words leading-relaxed">
                                    “{section.exposed_data}”
                                  </p>
                                </div>
                              )}

                              <div>
                                <span className="text-[10px] text-blue-400 font-extrabold uppercase tracking-widest block mb-1.5">Mitigazioni Consigliate</span>
                                <p className="text-gray-300 font-light leading-relaxed">
                                  {section.mitigation}
                                </p>
                              </div>
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="prose prose-invert max-w-none">
                       <p className="text-gray-300 leading-relaxed text-[15px] font-light">
                           {data.llm_report.mitigation_advice || "Nessun consiglio di mitigazione generato."}
                       </p>
                    </div>
                  )}
             </div>
          </div>
        )}
      </div>
    );
  }

  return null;
}

function AuthScreen({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isLogin) {
        const data = await login(email, password);
        localStorage.setItem('token', data.access_token);
        onLoginSuccess();
      } else {
        const formElement = e.target;
        const repeatPassword = formElement.repeat_password.value;
        if (password !== repeatPassword) {
          setError("Le password non coincidono");
          setLoading(false);
          return;
        }
        await register(email, password);
        const data = await login(email, password);
        localStorage.setItem('token', data.access_token);
        onLoginSuccess();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Errore di autenticazione");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      <div className="absolute top-[-10%] left-[-10%] w-[40rem] h-[40rem] bg-blue-600/20 rounded-full blur-3xl -z-10 mix-blend-screen"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40rem] h-[40rem] bg-purple-600/20 rounded-full blur-3xl -z-10 mix-blend-screen"></div>
      
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md z-10 flex flex-col items-center">
        <img 
          src="/logo.png" 
          alt="SEA - Social Exposure Analyzer" 
          className="w-64 h-auto mb-8 drop-shadow-[0_0_25px_rgba(139,92,246,0.4)] rounded-2xl" 
        />
        <Card className="glassmorphism w-full !bg-transparent border-white/10 p-8 shadow-2xl">
          <Title className="text-white text-2xl font-bold text-center mb-6">
            {isLogin ? "Accedi al tuo account" : "Crea un nuovo account"}
          </Title>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Text className="text-gray-300 mb-1">Email</Text>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-surface/50 border border-white/10 text-white px-4 py-2 rounded-lg outline-none"
                required
              />
            </div>
            <div>
              <Text className="text-gray-300 mb-1">Password</Text>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-surface/50 border border-white/10 text-white px-4 py-2 rounded-lg outline-none"
                required
              />
            </div>
            {!isLogin && (
              <div>
                <Text className="text-gray-300 mb-1">Ripeti Password</Text>
                <input
                  type="password"
                  name="repeat_password"
                  className="w-full bg-surface/50 border border-white/10 text-white px-4 py-2 rounded-lg outline-none"
                  required
                />
              </div>
            )}
            
            {error && <Text className="text-red-400 text-sm text-center">{error}</Text>}
            
            <button type="submit" disabled={loading} className="w-full bg-primary hover:bg-blue-600 text-white font-semibold py-3 rounded-lg transition-colors mt-4">
              {loading ? "Attendere..." : (isLogin ? "Login" : "Registrati")}
            </button>
          </form>
          
          <div className="mt-6 text-center">
            <button onClick={() => setIsLogin(!isLogin)} className="text-gray-400 hover:text-white text-sm transition-colors">
              {isLogin ? "Non hai un account? Registrati" : "Hai già un account? Accedi"}
            </button>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}

function MainApp({ onLogout }) {
  const [targetUrl, setTargetUrl] = useState('');
  const [analysisId, setAnalysisId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // OSINT Settings State
  const [enableDdg, setEnableDdg] = useState(true);
  const [enableHolehe, setEnableHolehe] = useState(true);
  const [enableIgScan, setEnableIgScan] = useState(false);
  const [igSessionId, setIgSessionId] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!targetUrl) return;
    setIsSubmitting(true);
    try {
      const res = await startAnalysis(
        targetUrl, 
        enableDdg, 
        enableHolehe, 
        enableIgScan ? igSessionId : null
      );
      setAnalysisId(res.analysis_id);
    } catch (err) {
        if(err.response?.status === 401) {
            onLogout();
        } else {
            alert("Errore nell'avvio dell'analisi.");
        }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center py-20 px-6 font-sans relative overflow-hidden">
      <div className="absolute top-4 right-6 z-20">
        <button onClick={onLogout} className="text-gray-400 hover:text-white text-sm border border-white/10 px-4 py-2 rounded-full glassmorphism">Logout</button>
      </div>

      {/* Background Decorativo */}
      <div className="absolute top-[-10%] left-[-10%] w-[40rem] h-[40rem] bg-blue-600/20 rounded-full blur-3xl -z-10 mix-blend-screen"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40rem] h-[40rem] bg-purple-600/20 rounded-full blur-3xl -z-10 mix-blend-screen"></div>

      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }} className="text-center max-w-3xl w-full z-10">
        <motion.img 
          src="/logo.png" 
          alt="SEA - Social Exposure Analyzer" 
          className="w-72 md:w-96 h-auto mx-auto mb-10 drop-shadow-[0_0_35px_rgba(139,92,246,0.5)] rounded-2xl" 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        />

        <form onSubmit={handleSubmit} className="relative group max-w-2xl mx-auto flex flex-col">
          <div className="relative">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full blur opacity-30 group-hover:opacity-60 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative flex items-center bg-surface border border-white/10 rounded-full p-2 shadow-2xl">
              <input
                type="text"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="Inserisci l'URL di un profilo social o uno username..."
                className="w-full bg-transparent text-white px-6 py-4 outline-none placeholder-gray-500 text-lg"
                disabled={isSubmitting || analysisId !== null}
              />
              {!analysisId && (
                <button type="submit" disabled={isSubmitting} className="bg-primary hover:bg-blue-600 text-white font-semibold py-4 px-10 rounded-full transition-colors flex-shrink-0 text-lg">
                  {isSubmitting ? 'Avvio...' : 'Scansiona'}
                </button>
              )}
              {analysisId && (
                <button type="button" onClick={() => { setAnalysisId(null); setTargetUrl(''); }} className="bg-white/10 hover:bg-white/20 text-white font-semibold py-4 px-10 rounded-full transition-colors flex-shrink-0 backdrop-blur-md border border-white/5 text-lg">
                  Reset
                </button>
              )}
            </div>
          </div>

          {!analysisId && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mt-8 flex flex-col space-y-4 text-left glassmorphism p-6 rounded-3xl mx-auto w-full max-w-lg border-white/5 shadow-2xl">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-bold text-sm tracking-widest uppercase mb-1">Moduli Sensori OSINT</h3>
                <span className="text-xs text-gray-400 bg-white/5 px-2 py-1 rounded">Advanced</span>
              </div>
              
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div>
                  <div className="text-gray-200 text-sm font-medium">DuckDuckGo Dorking</div>
                  <div className="text-gray-500 text-xs">Ricerca aggressiva per menzioni web e data leaks.</div>
                </div>
                <button type="button" onClick={() => setEnableDdg(!enableDdg)} className={`w-12 h-6 rounded-full transition-colors duration-300 focus:outline-none flex items-center px-1 ${enableDdg ? 'bg-blue-500' : 'bg-gray-600'}`}>
                  <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${enableDdg ? 'translate-x-6' : ''}`}></div>
                </button>
              </div>

              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div>
                  <div className="text-gray-200 text-sm font-medium">Holehe (Cross-Check Email)</div>
                  <div className="text-gray-500 text-xs">Verifica se l'email estratta è registrata su 120+ siti web.</div>
                </div>
                <button type="button" onClick={() => setEnableHolehe(!enableHolehe)} className={`w-12 h-6 rounded-full transition-colors duration-300 focus:outline-none flex items-center px-1 ${enableHolehe ? 'bg-blue-500' : 'bg-gray-600'}`}>
                  <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${enableHolehe ? 'translate-x-6' : ''}`}></div>
                </button>
              </div>

              <div className="flex items-center justify-between pb-1">
                <div>
                  <div className="text-gray-200 text-sm font-medium">Deep Scan Instagram</div>
                  <div className="text-gray-500 text-xs">Richiede un sessionid attivo (non salvato nel DB).</div>
                </div>
                <button type="button" onClick={() => setEnableIgScan(!enableIgScan)} className={`w-12 h-6 rounded-full transition-colors duration-300 focus:outline-none flex items-center px-1 ${enableIgScan ? 'bg-purple-500' : 'bg-gray-600'}`}>
                  <div className={`w-4 h-4 rounded-full bg-white transform transition-transform duration-300 ${enableIgScan ? 'translate-x-6' : ''}`}></div>
                </button>
              </div>

              <AnimatePresence>
                {enableIgScan && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                    <input
                      type="text"
                      value={igSessionId}
                      onChange={(e) => setIgSessionId(e.target.value)}
                      placeholder="sessionid (es. 123456789%3AABCDE...)"
                      className="w-full mt-2 bg-black/30 border border-purple-500/30 text-white px-4 py-2 rounded-lg outline-none text-xs focus:border-purple-500 transition-colors placeholder-gray-600"
                    />
                  </motion.div>
                )}
              </AnimatePresence>

            </motion.div>
          )}

        </form>
      </motion.div>

      <AnimatePresence mode="wait">
        {analysisId && (
          <ErrorBoundary key={analysisId}>
            <Dashboard analysisId={analysisId} />
          </ErrorBoundary>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  return (
    <QueryClientProvider client={queryClient}>
      {isAuthenticated ? (
        <MainApp onLogout={handleLogout} />
      ) : (
        <AuthScreen onLoginSuccess={() => setIsAuthenticated(true)} />
      )}
    </QueryClientProvider>
  );
}
