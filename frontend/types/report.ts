// Types for the edit overlay system

export interface LineMapping {
  line_number: number;
  source_code: string;
  original_text: string;
}

export interface EditEntry {
  originalText: string;
  editedText: string;
  sourceCode: string;
  lineNumber: number;
}

export interface ManualAddition {
  afterLine: number;
  text: string;
}

export interface GeneratedReportResponse {
  report_text: string;
  parsed_data: Record<string, any>;
  validation_errors: string[];
  line_mappings: LineMapping[];
}