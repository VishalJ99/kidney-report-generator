import { EditEntry, ManualAddition, LineMapping } from '@/types/report';

/**
 * Detects edits between original and edited report text
 * Returns edit overlay entries and manual additions
 */
export function detectEdits(
  originalReport: string,
  editedReport: string,
  lineMappings: LineMapping[]
): {
  editOverlay: Map<number, EditEntry>;
  manualAdditions: ManualAddition[];
} {
  const editOverlay = new Map<number, EditEntry>();
  const manualAdditions: ManualAddition[] = [];
  
  const originalLines = originalReport.split('\n');
  const editedLines = editedReport.split('\n');
  
  // Create a map of line number to source code for quick lookup
  const lineToSource = new Map<number, string>();
  lineMappings.forEach(mapping => {
    lineToSource.set(mapping.line_number, mapping.source_code);
  });
  
  // Track edits for existing lines
  const minLength = Math.min(originalLines.length, editedLines.length);
  
  for (let i = 0; i < minLength; i++) {
    const lineNumber = i + 1;
    const originalLine = originalLines[i];
    const editedLine = editedLines[i];
    
    if (originalLine !== editedLine) {
      // Line was edited
      const sourceCode = lineToSource.get(lineNumber) || '';
      
      editOverlay.set(lineNumber, {
        originalText: originalLine,
        editedText: editedLine,
        sourceCode: sourceCode,
        lineNumber: lineNumber
      });
    }
  }
  
  // Handle added lines at the end
  if (editedLines.length > originalLines.length) {
    for (let i = originalLines.length; i < editedLines.length; i++) {
      manualAdditions.push({
        afterLine: originalLines.length,
        text: editedLines[i]
      });
    }
  }
  
  return { editOverlay, manualAdditions };
}

/**
 * Identifies which lines have edits for visual highlighting
 */
export function getEditedLineNumbers(
  editOverlay: Map<number, EditEntry>,
  manualAdditions: ManualAddition[]
): Set<number> {
  const editedLines = new Set<number>();
  
  // Add lines from edit overlay
  editOverlay.forEach((_, lineNumber) => {
    editedLines.add(lineNumber);
  });
  
  // Add lines from manual additions
  manualAdditions.forEach(addition => {
    // Manual additions don't have a specific line number yet
    // They'll be highlighted differently
  });
  
  return editedLines;
}

/**
 * Determines if a specific line is an edit or a manual addition
 */
export function getLineStatus(
  lineNumber: number,
  editOverlay: Map<number, EditEntry>,
  manualAdditionStartLine: number
): 'original' | 'edited' | 'added' {
  if (editOverlay.has(lineNumber)) {
    return 'edited';
  }
  
  if (lineNumber >= manualAdditionStartLine) {
    return 'added';
  }
  
  return 'original';
}