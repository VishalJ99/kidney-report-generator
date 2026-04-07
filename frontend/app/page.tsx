'use client';

import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import ShorthandInput from '@/components/ShorthandInput';
import ReportPreview from '@/components/ReportPreview';
import QuickActions from '@/components/QuickActions';
import MappingReference from '@/components/MappingReference';
import PhraseManager from '@/components/PhraseManager';
import CaseCodesPanel from '@/components/CaseCodesPanel';
import { usePhraseMappings } from '@/hooks/usePhraseMappings';

interface CaseCode {
  key: string;
  section: string;
  label: string;
  codes: Record<string, string>;
  pending_code_types: string[];
}

interface PhraseEntry {
  key: string;
  main_body: string;
  conclusion: string;
  comments: string;
  codes: Record<string, string>;
}

const API_URL = '';

const EXAMPLE_SHORTHAND = `NHS 234 4567 2345
HN 31098674
NS 25-67890
Name Smith
Coder CR
Consent PISv.8
Date 12/07/2025
!LM
CM
C2M1
!G
TG31 GS7 SS1_NOS MM1 MC1 G2 CG1
!T
ATI_MICRO IFTA20 CTCI1 T1 I1_I-IFTA3 TI2
!BV
A3 2IL_1AR CV2 CAA0 V0 AH1 PTC1
!IHC
C4D0 SV40_0
!EM
EM0
!IF
FR0
!CONC
BL MVI MILD-IFTA
!COM
MVI-C4D0-DSA0 DP`;

export default function Home() {
  const [reportType, setReportType] = useState<'transplant' | 'native'>('transplant');
  const [shorthandText, setShorthandText] = useState('');
  const [generatedReport, setGeneratedReport] = useState('');
  const [caseCodes, setCaseCodes] = useState<CaseCode[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isReferenceOpen, setIsReferenceOpen] = useState(false);
  const [isPhraseManagerOpen, setIsPhraseManagerOpen] = useState(false);
  const [phraseEntries, setPhraseEntries] = useState<PhraseEntry[]>([]);
  const [isPhraseEntriesLoading, setIsPhraseEntriesLoading] = useState(false);
  const [phraseEntriesError, setPhraseEntriesError] = useState<string | null>(null);

  const { mappings, refresh: refreshMappings } = usePhraseMappings(reportType);

  const generateReport = useCallback(async () => {
    if (!shorthandText.trim()) {
      setGeneratedReport('');
      setCaseCodes([]);
      return;
    }

    setIsGenerating(true);
    try {
      const response = await axios.post(`${API_URL}/api/generate`, {
        shorthand_text: shorthandText,
        report_type: reportType,
      });

      setGeneratedReport(response.data.report_text);
      setCaseCodes(response.data.case_codes || []);
    } catch (error: any) {
      console.error('Error generating report:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate report');
    } finally {
      setIsGenerating(false);
    }
  }, [shorthandText, reportType]);

  const loadPhraseEntries = useCallback(async () => {
    try {
      setIsPhraseEntriesLoading(true);
      setPhraseEntriesError(null);
      const response = await axios.get(`${API_URL}/api/phrases/entries`);
      setPhraseEntries(response.data || []);
    } catch (error) {
      console.error('Error loading phrase entries:', error);
      setPhraseEntries([]);
      setPhraseEntriesError('Failed to load phrase entries');
    } finally {
      setIsPhraseEntriesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!shorthandText.trim()) {
      setGeneratedReport('');
      setCaseCodes([]);
      return;
    }

    const timer = setTimeout(() => {
      void generateReport();
    }, 25);

    return () => clearTimeout(timer);
  }, [generateReport]);

  useEffect(() => {
    void loadPhraseEntries();
  }, [loadPhraseEntries]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab' && !isPhraseManagerOpen) {
        e.preventDefault();
        setIsReferenceOpen((prev) => !prev);
      } else if (e.key === 'Escape') {
        if (isPhraseManagerOpen) {
          setIsPhraseManagerOpen(false);
        } else if (isReferenceOpen) {
          setIsReferenceOpen(false);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isPhraseManagerOpen, isReferenceOpen]);

  const handleCopyReport = () => {
    if (generatedReport) {
      navigator.clipboard.writeText(generatedReport);
      toast.success('Report copied to clipboard!');
    }
  };

  const handleClear = () => {
    setShorthandText('');
    setGeneratedReport('');
    setCaseCodes([]);
  };

  const handleLoadExample = () => {
    setShorthandText(EXAMPLE_SHORTHAND);
  };

  const handleSavePhraseEntry = useCallback(
    async (entry: PhraseEntry) => {
      const normalizedKey = entry.key.trim().toLowerCase();
      if (!normalizedKey) {
        toast.error('Shorthand key is required');
        return;
      }

      try {
        await axios.put(`${API_URL}/api/phrases/entries/${encodeURIComponent(normalizedKey)}`, {
          main_body: entry.main_body,
          conclusion: entry.conclusion,
          comments: entry.comments,
          codes: {
            native1: entry.codes.native1 || '',
            transplant: entry.codes.transplant || '',
            kbc: entry.codes.kbc || '',
          },
        });

        toast.success(`Saved phrase entry: ${normalizedKey}`);
        await Promise.all([
          loadPhraseEntries(),
          refreshMappings(),
          shorthandText.trim() ? generateReport() : Promise.resolve(),
        ]);
      } catch (error: any) {
        console.error('Error saving phrase entry:', error);
        toast.error(error.response?.data?.detail || 'Failed to save phrase entry');
      }
    },
    [generateReport, loadPhraseEntries, refreshMappings, shorthandText],
  );

  const handleDeletePhraseEntry = useCallback(
    async (phraseKey: string) => {
      const normalizedKey = phraseKey.trim().toLowerCase();
      if (!normalizedKey) {
        toast.error('Shorthand key is required');
        return;
      }

      try {
        await axios.delete(`${API_URL}/api/phrases/entries/${encodeURIComponent(normalizedKey)}`);
        toast.success(`Deleted phrase entry: ${normalizedKey}`);
        await Promise.all([
          loadPhraseEntries(),
          refreshMappings(),
          shorthandText.trim() ? generateReport() : Promise.resolve(),
        ]);
      } catch (error: any) {
        console.error('Error deleting phrase entry:', error);
        toast.error(error.response?.data?.detail || 'Failed to delete phrase entry');
      }
    },
    [generateReport, loadPhraseEntries, refreshMappings, shorthandText],
  );

  const handleExportCSV = () => {
    toast('CSV export coming soon!', {
      icon: 'i',
    });
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />

      <MappingReference isOpen={isReferenceOpen} mappings={mappings} />
      <PhraseManager
        isOpen={isPhraseManagerOpen}
        entries={phraseEntries}
        isLoading={isPhraseEntriesLoading}
        error={phraseEntriesError}
        onClose={() => setIsPhraseManagerOpen(false)}
        onSave={handleSavePhraseEntry}
        onDelete={handleDeletePhraseEntry}
        downloadUrl="/api/phrases/download"
      />

      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            Kidney Biopsy Report Generator
          </h1>
          <p className="text-gray-600 mt-2">
            Generate standardized kidney biopsy reports from shorthand notation
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Report Type</h2>
              <div className="flex gap-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="transplant"
                    checked={reportType === 'transplant'}
                    onChange={(e) => setReportType(e.target.value as 'transplant' | 'native')}
                    className="mr-2"
                  />
                  <span>Transplant</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="native"
                    checked={reportType === 'native'}
                    onChange={(e) => setReportType(e.target.value as 'transplant' | 'native')}
                    className="mr-2"
                  />
                  <span>Native</span>
                </label>
              </div>
            </div>

            <ShorthandInput
              value={shorthandText}
              onChange={setShorthandText}
              onLoadExample={handleLoadExample}
            />

            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setIsReferenceOpen(true)}
                className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded hover:bg-gray-100"
              >
                Reference
              </button>
              <button
                onClick={() => setIsPhraseManagerOpen(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Manage dictionary
              </button>
              <button
                onClick={handleClear}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="space-y-6">
            <ReportPreview
              report={generatedReport}
              isGenerating={isGenerating}
            />

            <QuickActions
              onCopy={handleCopyReport}
              onExportCSV={handleExportCSV}
              disabled={!generatedReport}
            />

            <CaseCodesPanel
              codes={caseCodes}
              reportType={reportType}
            />
          </div>
        </div>

        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>Kidney Biopsy Report Generator v1.0.0</p>
          <p>Designed for clinical pathologists to streamline report generation</p>
        </footer>
      </div>
    </main>
  );
}
