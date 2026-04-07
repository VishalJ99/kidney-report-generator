'use client';

import { useEffect, useMemo, useState } from 'react';

interface PhraseEntry {
  key: string;
  main_body: string;
  conclusion: string;
  comments: string;
  codes: Record<string, string>;
}

interface PhraseManagerProps {
  isOpen: boolean;
  entries: PhraseEntry[];
  isLoading: boolean;
  error: string | null;
  onClose: () => void;
  onSave: (entry: PhraseEntry) => Promise<void>;
  onDelete: (phraseKey: string) => Promise<void>;
  downloadUrl: string;
}

const EMPTY_ENTRY: PhraseEntry = {
  key: '',
  main_body: '',
  conclusion: '',
  comments: '',
  codes: {
    native1: '',
    transplant: '',
    kbc: '',
  },
};

const normalizeEntry = (entry?: PhraseEntry): PhraseEntry => ({
  ...EMPTY_ENTRY,
  ...entry,
  codes: {
    ...EMPTY_ENTRY.codes,
    ...(entry?.codes || {}),
  },
});

export default function PhraseManager({
  isOpen,
  entries,
  isLoading,
  error,
  onClose,
  onSave,
  onDelete,
  downloadUrl,
}: PhraseManagerProps) {
  const [search, setSearch] = useState('');
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [form, setForm] = useState<PhraseEntry>(EMPTY_ENTRY);
  const [isSaving, setIsSaving] = useState(false);

  const filteredEntries = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return entries;
    }

    return entries.filter((entry) => {
      return (
        entry.key.toLowerCase().includes(query) ||
        entry.main_body.toLowerCase().includes(query) ||
        entry.conclusion.toLowerCase().includes(query) ||
        entry.comments.toLowerCase().includes(query)
      );
    });
  }, [entries, search]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    if (selectedKey) {
      const selectedEntry = entries.find((entry) => entry.key === selectedKey);
      if (selectedEntry) {
        setForm(normalizeEntry(selectedEntry));
        return;
      }
    }

    setForm((current) => normalizeEntry(current.key ? current : EMPTY_ENTRY));
  }, [entries, isOpen, selectedKey]);

  if (!isOpen) {
    return null;
  }

  const handleSelectEntry = (entry: PhraseEntry) => {
    setSelectedKey(entry.key);
    setForm(normalizeEntry(entry));
  };

  const handleNewEntry = () => {
    setSelectedKey(null);
    setForm(EMPTY_ENTRY);
  };

  const handleChange = (field: keyof Omit<PhraseEntry, 'codes'>, value: string) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleCodeChange = (field: 'native1' | 'transplant' | 'kbc', value: string) => {
    setForm((current) => ({
      ...current,
      codes: {
        ...current.codes,
        [field]: value,
      },
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(normalizeEntry(form));
      setSelectedKey(form.key.trim().toLowerCase() || null);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedKey) {
      return;
    }

    const confirmed = window.confirm(`Delete phrase entry "${selectedKey}"?`);
    if (!confirmed) {
      return;
    }

    setIsSaving(true);
    try {
      await onDelete(selectedKey);
      setSelectedKey(null);
      setForm(EMPTY_ENTRY);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="grid h-[90vh] w-full max-w-7xl grid-cols-1 overflow-hidden rounded-xl bg-white shadow-2xl lg:grid-cols-[320px_1fr]">
        <aside className="border-b border-gray-200 bg-gray-50 p-4 lg:border-b-0 lg:border-r">
          <div className="mb-4 flex items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Phrase dictionary</h2>
              <p className="text-sm text-gray-500">Edit the runtime shorthand source of truth.</p>
            </div>
            <button
              onClick={onClose}
              className="rounded border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100"
            >
              Close
            </button>
          </div>

          <div className="mb-3 space-y-2">
            <button
              onClick={handleNewEntry}
              className="w-full rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              New entry
            </button>
            <a
              href={downloadUrl}
              download="phrases_sectioned.json"
              className="block w-full rounded border border-gray-300 bg-white px-3 py-2 text-center text-sm font-medium text-gray-700 hover:bg-gray-100"
            >
              Download JSON backup
            </a>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search shorthand or text"
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div className="mb-3 rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
            Writes update the live dictionary immediately and persist on the Railway backend volume. They do not automatically sync back to git or the Excel source workbook, so download a JSON backup when needed.
          </div>

          <div className="h-[calc(90vh-240px)] overflow-y-auto rounded border border-gray-200 bg-white">
            {isLoading ? (
              <div className="p-3 text-sm text-gray-500">Loading phrase entries...</div>
            ) : error ? (
              <div className="p-3 text-sm text-red-600">{error}</div>
            ) : filteredEntries.length === 0 ? (
              <div className="p-3 text-sm text-gray-500">No phrase entries match the current search.</div>
            ) : (
              filteredEntries.map((entry) => {
                const isSelected = entry.key === selectedKey;
                return (
                  <button
                    key={entry.key}
                    onClick={() => handleSelectEntry(entry)}
                    className={`block w-full border-b border-gray-100 px-3 py-3 text-left last:border-b-0 ${
                      isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="text-sm font-semibold text-gray-900">{entry.key}</div>
                    <div className="mt-1 overflow-hidden text-ellipsis whitespace-nowrap text-xs text-gray-500">
                      {entry.conclusion || entry.main_body || entry.comments || 'No text configured'}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </aside>

        <section className="overflow-y-auto p-6">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-900">
              {selectedKey ? `Edit ${selectedKey}` : 'Create a shorthand entry'}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Configure section-specific expansions and any available diagnostic code values.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Shorthand key</span>
              <input
                type="text"
                value={form.key}
                onChange={(e) => handleChange('key', e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                placeholder="e.g. mpgn-ic"
              />
            </label>

            <div className="rounded border border-gray-200 bg-gray-50 p-4">
              <div className="text-sm font-medium text-gray-700">Code families</div>
              <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
                <label className="block">
                  <span className="mb-2 block text-sm text-gray-600">native1</span>
                  <input
                    type="text"
                    value={form.codes.native1 || ''}
                    onChange={(e) => handleCodeChange('native1', e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="46826"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-gray-600">transplant</span>
                  <input
                    type="text"
                    value={form.codes.transplant || ''}
                    onChange={(e) => handleCodeChange('transplant', e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="Banff or registry code"
                  />
                </label>
                <label className="block">
                  <span className="mb-2 block text-sm text-gray-600">kbc</span>
                  <input
                    type="text"
                    value={form.codes.kbc || ''}
                    onChange={(e) => handleCodeChange('kbc', e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                    placeholder="16"
                  />
                </label>
              </div>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Main body</span>
              <textarea
                value={form.main_body}
                onChange={(e) => handleChange('main_body', e.target.value)}
                rows={4}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Conclusion</span>
              <textarea
                value={form.conclusion}
                onChange={(e) => handleChange('conclusion', e.target.value)}
                rows={4}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Comments</span>
              <textarea
                value={form.comments}
                onChange={(e) => handleChange('comments', e.target.value)}
                rows={6}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            </label>
          </div>

          <div className="mt-6 flex flex-wrap gap-2">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSaving ? 'Saving...' : 'Save entry'}
            </button>
            {selectedKey && (
              <button
                onClick={handleDelete}
                disabled={isSaving}
                className="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSaving ? 'Working...' : 'Delete entry'}
              </button>
            )}
            <button
              onClick={handleNewEntry}
              className="rounded border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            >
              Reset form
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
