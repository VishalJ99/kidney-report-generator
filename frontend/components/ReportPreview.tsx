import React, { useCallback, useRef, useEffect } from 'react';
import { EditEntry, ManualAddition } from '@/types/report';
import { getLineStatus } from '@/utils/editDetector';

interface ReportPreviewProps {
  report: string;
  editableReport: string;
  isGenerating: boolean;
  isEditMode: boolean;
  onToggleEditMode: () => void;
  onReportEdit: (editedText: string) => void;
  editOverlay: Map<number, EditEntry>;
  manualAdditions: ManualAddition[];
}

const ReportPreview: React.FC<ReportPreviewProps> = ({ 
  report, 
  editableReport,
  isGenerating,
  isEditMode,
  onToggleEditMode,
  onReportEdit,
  editOverlay,
  manualAdditions 
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Auto-resize textarea to fit content
  useEffect(() => {
    if (textareaRef.current && isEditMode) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [editableReport, isEditMode]);
  
  const handleTextChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onReportEdit(e.target.value);
  }, [onReportEdit]);
  
  // Apply line-specific styling
  const getLineClassName = useCallback((lineNumber: number) => {
    const status = getLineStatus(
      lineNumber, 
      editOverlay, 
      report.split('\n').length + 1
    );
    
    switch (status) {
      case 'edited':
        return 'edited-line';
      case 'added':
        return 'manual-addition';
      default:
        return '';
    }
  }, [editOverlay, report]);
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Generated Report</h2>
        {report && (
          <button
            onClick={onToggleEditMode}
            className={`px-3 py-1 rounded transition-colors ${
              isEditMode 
                ? 'bg-amber-500 text-white hover:bg-amber-600' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {isEditMode ? 'View Only' : 'Edit Report'}
          </button>
        )}
      </div>
      
      <div className="relative">
        <div className="report-preview bg-gray-50 rounded-lg p-6 min-h-[600px] max-h-[800px] overflow-y-auto border border-gray-200">
          {report ? (
            isEditMode ? (
              <textarea
                ref={textareaRef}
                value={editableReport}
                onChange={handleTextChange}
                className="w-full text-sm text-gray-800 font-mono bg-transparent border-none outline-none resize-none report-editable"
                style={{ minHeight: '600px' }}
              />
            ) : (
              <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono report-display">
                {report}
              </pre>
            )
          ) : (
            <div className="text-gray-400 text-center mt-20">
              <svg
                className="mx-auto h-12 w-12 text-gray-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="mt-4">Report will appear here</p>
              <p className="text-sm mt-2">Enter shorthand notation to generate</p>
            </div>
          )}
        </div>
        
        {report && (
          <div className="absolute top-2 right-2 flex gap-2">
            {isEditMode && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                Editing
              </span>
            )}
            {editOverlay.size > 0 && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {editOverlay.size} edits
              </span>
            )}
            {manualAdditions.length > 0 && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                {manualAdditions.length} additions
              </span>
            )}
            {!isEditMode && editOverlay.size === 0 && manualAdditions.length === 0 && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Ready
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPreview;