import { useState } from 'react';
import { useQuery, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, Text, Metric, Flex, ProgressBar, Title, BarChart } from '@tremor/react';
import { startAnalysis, getAnalysisStatus } from './api';

const queryClient = new QueryClient();

function Dashboard({ analysisId }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => getAnalysisStatus(analysisId),
    refetchInterval: (data) => {
      // Polling ogni 3 secondi se non completato
      if (!data) return 3000;
      return data.status === 'PENDING' ? 3000 : false;
    },
  });

  if (isLoading || (data && data.status === 'PENDING')) {
    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center justify-center p-12 glassmorphism rounded-2xl mt-8">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
        <Title className="text-white">Analisi in corso...</Title>
        <Text className="text-gray-400">Scraping OSINT e processamento NLP in esecuzione</Text>
      </motion.div>
    );
  }

  if (isError || data?.status === 'FAILED') {
    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="p-8 bg-red-900/20 border border-red-500/50 rounded-2xl mt-8 text-center">
         <Title className="text-red-400">Analisi Fallita</Title>
         <Text className="text-red-300">{data?.error_message || "Si è verificato un errore di rete."}</Text>
      </motion.div>
    );
  }

  if (data?.status === 'COMPLETED') {
    const chartData = [
      { name: 'Rischio Calcolato', Score: data.risk_score || 0 }
    ];

    const isCritical = data.risk_level === 'CRITICAL' || data.risk_level === 'HIGH';

    return (
      <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mt-8 space-y-6 w-full max-w-4xl text-left">
        <Card className="glassmorphism !bg-transparent !ring-0 !border-white/10">
          <Flex alignItems="start">
            <div>
              <Text className="text-gray-400 font-medium tracking-wide uppercase text-xs">Risk Score Globale</Text>
              <Metric className="text-white text-5xl font-bold mt-1">{data.risk_score} / 100</Metric>
            </div>
            <div className={`px-4 py-1.5 rounded-full text-sm font-bold tracking-wider ${isCritical ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
              {data.risk_level}
            </div>
          </Flex>
          <ProgressBar value={data.risk_score} color={isCritical ? 'red' : 'blue'} className="mt-6" />
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="glassmorphism !bg-transparent !ring-0 !border-white/10">
              <Title className="text-white mb-6">Indice di Rischio</Title>
              <BarChart
                data={chartData}
                index="name"
                categories={["Score"]}
                colors={isCritical ? ["red"] : ["blue"]}
                className="h-48"
                showAnimation={true}
              />
            </Card>

            <Card className="glassmorphism !bg-transparent !ring-0 !border-white/10">
              <Title className="text-white mb-4">Dati Sensibili (PII) Rilevati</Title>
              <div className="space-y-3 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                {(!data.pii_extracted || data.pii_extracted.length === 0) ? (
                  <Text className="text-gray-400 italic">Nessun dato sensibile rilevato.</Text>
                ) : (
                  data.pii_extracted.map((pii, idx) => (
                    <div key={idx} className="flex justify-between items-center p-3 rounded-lg bg-surface/80 border border-white/5 shadow-inner">
                      <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">{pii.label}</span>
                      <span className="text-white text-sm font-medium">{pii.value}</span>
                    </div>
                  ))
                )}
              </div>
            </Card>
        </div>

        {data.llm_report && (
          <Card className="glassmorphism !bg-transparent !ring-0 !border-white/10">
             <Title className="text-white mb-4 text-xl">Audit di Sicurezza (AI)</Title>
             <div className="prose prose-invert max-w-none">
                <Text className="text-gray-300 leading-relaxed text-base">
                    {data.llm_report.mitigation_advice}
                </Text>
             </div>
          </Card>
        )}
      </motion.div>
    );
  }

  return null;
}

function MainApp() {
  const [targetUrl, setTargetUrl] = useState('');
  const [analysisId, setAnalysisId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!targetUrl) return;
    setIsSubmitting(true);
    try {
      const res = await startAnalysis(targetUrl);
      setAnalysisId(res.analysis_id);
    } catch (err) {
      alert("Errore nell'avvio dell'analisi. Controlla che il backend sia attivo.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center py-20 px-6 font-sans relative overflow-hidden">
      {/* Background Decorativo */}
      <div className="absolute top-[-10%] left-[-10%] w-[40rem] h-[40rem] bg-blue-600/20 rounded-full blur-3xl -z-10 mix-blend-screen"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40rem] h-[40rem] bg-purple-600/20 rounded-full blur-3xl -z-10 mix-blend-screen"></div>

      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }} className="text-center max-w-3xl w-full z-10">
        <h1 className="text-5xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 mb-6 tracking-tight drop-shadow-lg">
          Social Exposure
        </h1>
        <p className="text-gray-400 mb-12 text-lg md:text-xl font-light">
          Valutazione automatica del rischio di social engineering tramite <strong className="text-white font-medium">OSINT</strong> e <strong className="text-white font-medium">AI</strong>.
        </p>

        <form onSubmit={handleSubmit} className="relative group max-w-2xl mx-auto">
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
        </form>
      </motion.div>

      <AnimatePresence mode="wait">
        {analysisId && <Dashboard key={analysisId} analysisId={analysisId} />}
      </AnimatePresence>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MainApp />
    </QueryClientProvider>
  );
}
