'use client';

import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import PatientInfo from '@/components/PatientInfo';
import ShorthandInput from '@/components/ShorthandInput';
import ReportPreview from '@/components/ReportPreview';
import QuickActions from '@/components/QuickActions';
import { EditEntry, ManualAddition, GeneratedReportResponse, LineMapping } from '@/types/report';
import { detectEdits } from '@/utils/editDetector';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Example shorthand for demo
const EXAMPLE_SHORTHAND = `NHS: 234 4567 2345
HN: 31098674
NS: 25-67890
Name: Smith
Coder: CR
Consent: PISv.8
Date of biopsy: 12/07/2025
LM: CM, C2M1
Glom: 31, Gs7, Ss1_NOS, Mm1, Mc1, G2, Cg1
TI: ATI micro, IFTA20, CTCI1, T1, I1_I-IFTA3, TI2
Ves: A3, 2IL_1Ar, Cv2, Caa0, V0, Ah1, Ptc1
IHC: C4d0, SV40_0
EM: EM0
IFFR: FR_0
CONCLUSION: BL, MVI+, MildIFTA
COMMENT: MVI+, DP`;

export default function Home() {
  const [reportType, setReportType] = useState<'transplant' | 'native'>('transplant');
  const [shorthandText, setShorthandText] = useState('');
  const [generatedReport, setGeneratedReport] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Edit overlay system state
  const [editOverlay, setEditOverlay] = useState<Map<number, EditEntry>>(new Map());
  const [manualAdditions, setManualAdditions] = useState<ManualAddition[]>([]);
  const [isEditMode, setIsEditMode] = useState(false);
  const [lineMappings, setLineMappings] = useState<LineMapping[]>([]);
  const [editableReport, setEditableReport] = useState('');

  // Streaming report generation (near-instant)
  useEffect(() => {
    // Clear report immediately when input is empty
    if (!shorthandText.trim()) {
      setGeneratedReport('');
      return;
    }

    const timer = setTimeout(() => {
      generateReport();
    }, 25);  // 25ms for smooth streaming feel (40 updates/second)

    return () => clearTimeout(timer);
  }, [shorthandText]);

  const captureCurrentEdits = useCallback(() => {
    if (isEditMode && generatedReport && editableReport) {
      // Capture edits if we're in edit mode
      const { editOverlay: newOverlay, manualAdditions: newAdditions } = detectEdits(
        generatedReport,
        editableReport,
        lineMappings
      );
      setEditOverlay(newOverlay);
      setManualAdditions(newAdditions);
      return { newOverlay, newAdditions };
    }
    return { newOverlay: editOverlay, newAdditions: manualAdditions };
  }, [isEditMode, generatedReport, editableReport, lineMappings, editOverlay, manualAdditions]);

  const applyEditOverlay = useCallback((baseReport: string, overlay: Map<number, EditEntry>, additions: ManualAddition[]) => {
    // Split report into lines
    const lines = baseReport.split('\n');
    
    // Apply edits from overlay
    const editedLines = lines.map((line, index) => {
      const lineNumber = index + 1;
      const edit = overlay.get(lineNumber);
      return edit ? edit.editedText : line;
    });
    
    // Apply manual additions (sorted by position)
    const sortedAdditions = [...additions].sort((a, b) => a.afterLine - b.afterLine);
    let result = [...editedLines];
    let offset = 0;
    
    for (const addition of sortedAdditions) {
      const insertIndex = addition.afterLine + offset;
      result.splice(insertIndex, 0, addition.text);
      offset++;
    }
    
    return result.join('\n');
  }, []);

  const generateReport = useCallback(async () => {
    if (!shorthandText.trim()) {
      setGeneratedReport('');
      setEditableReport('');
      return;
    }

    // Capture current edits before regenerating
    const { newOverlay, newAdditions } = captureCurrentEdits();

    setIsGenerating(true);
    try {
      const response = await axios.post<GeneratedReportResponse>(`${API_URL}/api/generate`, {
        shorthand_text: shorthandText,
        report_type: reportType,
      });

      // Store line mappings
      setLineMappings(response.data.line_mappings || []);
      
      // Apply edit overlay with captured edits
      const finalReport = newOverlay.size > 0 || newAdditions.length > 0
        ? applyEditOverlay(response.data.report_text, newOverlay, newAdditions)
        : response.data.report_text;
      
      setGeneratedReport(finalReport);
      setEditableReport(finalReport);
    } catch (error: any) {
      console.error('Error generating report:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate report');
    } finally {
      setIsGenerating(false);
    }
  }, [shorthandText, reportType, captureCurrentEdits, applyEditOverlay]);

  const handleCopyReport = () => {
    if (generatedReport) {
      navigator.clipboard.writeText(generatedReport);
      toast.success('Report copied to clipboard!');
    }
  };

  const handleClear = () => {
    setShorthandText('');
    setGeneratedReport('');
    setEditableReport('');
    setEditOverlay(new Map());
    setManualAdditions([]);
    setLineMappings([]);
    setIsEditMode(false);
  };
  
  const handleReportEdit = useCallback((editedText: string) => {
    setEditableReport(editedText);
    // Edit detection will be handled by the utility function we'll create
  }, []);
  
  const toggleEditMode = useCallback(() => {
    if (isEditMode) {
      // Leaving edit mode - capture edits before switching
      const { editOverlay: newOverlay, manualAdditions: newAdditions } = detectEdits(
        generatedReport,
        editableReport,
        lineMappings
      );
      setEditOverlay(newOverlay);
      setManualAdditions(newAdditions);
      toast.success('Edit mode disabled - changes preserved');
    } else {
      // Entering edit mode
      toast.success('Edit mode enabled - changes will be preserved');
    }
    setIsEditMode(prev => !prev);
  }, [isEditMode, generatedReport, editableReport, lineMappings]);

  const handleLoadExample = () => {
    setShorthandText(EXAMPLE_SHORTHAND);
  };

  const handleExportCSV = () => {
    // TODO: Implement CSV export
    toast('CSV export coming soon!', {
      icon: 'ℹ️',
    });
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            🔬 Kidney Biopsy Report Generator
          </h1>
          <p className="text-gray-600 mt-2">
            Generate standardized kidney biopsy reports from shorthand notation
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="space-y-6">
            {/* Report Type Selection */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Report Type</h2>
              <div className="flex gap-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="transplant"
                    checked={reportType === 'transplant'}
                    onChange={(e) => setReportType(e.target.value as 'transplant')}
                    className="mr-2"
                  />
                  <span>Transplant</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="native"
                    checked={reportType === 'native'}
                    onChange={(e) => setReportType(e.target.value as 'native')}
                    className="mr-2"
                    disabled
                  />
                  <span className="text-gray-400">Native (Coming Soon)</span>
                </label>
              </div>
            </div>

            {/* Shorthand Input */}
            <ShorthandInput
              value={shorthandText}
              onChange={setShorthandText}
              onLoadExample={handleLoadExample}
            />

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={handleClear}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Output Section */}
          <div className="space-y-6">
            <ReportPreview
              report={generatedReport}
              editableReport={editableReport}
              isGenerating={isGenerating}
              isEditMode={isEditMode}
              onToggleEditMode={toggleEditMode}
              onReportEdit={handleReportEdit}
              editOverlay={editOverlay}
              manualAdditions={manualAdditions}
            />
            
            <QuickActions
              onCopy={handleCopyReport}
              onExportCSV={handleExportCSV}
              disabled={!generatedReport}
            />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>Kidney Biopsy Report Generator v1.0.0</p>
          <p>Designed for clinical pathologists to streamline report generation</p>
        </footer>
      </div>
    </main>
  );
}