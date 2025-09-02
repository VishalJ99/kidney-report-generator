import React from 'react';

interface ReportPreviewProps {
  report: string;
  isGenerating: boolean;
}

const ReportPreview: React.FC<ReportPreviewProps> = ({ report, isGenerating }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Generated Report</h2>
      </div>
      
      <div className="relative">
        <div className="report-preview bg-gray-50 rounded-lg p-6 min-h-[600px] max-h-[800px] overflow-y-auto border border-gray-200">
          {report ? (
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
              {report}
            </pre>
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
          <div className="absolute top-2 right-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              Ready
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPreview;