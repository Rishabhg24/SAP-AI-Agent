import React, { useState, useEffect, useRef } from 'react';
import {
  Calendar,
  ChevronDown,
  Check,
  RotateCcw,
  SlidersHorizontal,
  ArrowRight,
  X
} from 'lucide-react';

export interface CustomDaysFilterProps {
  selectedDays: number | null; // null = 'All time', number = past N days
  onApply: (days: number | null, label: string) => void;
  activeLabel?: string;
  loading?: boolean;
}

const PRESETS = [
  { label: 'All time', days: null, badge: 'All' },
  { label: 'Last 7 days', days: 7, badge: '7d' },
  { label: 'Last 14 days', days: 14, badge: '14d' },
  { label: 'Last 30 days', days: 30, badge: '30d' },
  { label: 'Last 90 days', days: 90, badge: '90d' },
  { label: 'Last 180 days', days: 180, badge: '180d' },
  { label: 'Last 365 days', days: 365, badge: '1y' },
];

export const CustomDaysFilter: React.FC<CustomDaysFilterProps> = ({
  selectedDays,
  onApply,
  activeLabel,
  loading = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [customDaysVal, setCustomDaysVal] = useState<string>(
    selectedDays !== null ? String(selectedDays) : '30'
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setIsCustomMode(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      const isStandard = PRESETS.some((p) => p.days === selectedDays);
      if (!isStandard && selectedDays !== null) {
        setIsCustomMode(true);
        setCustomDaysVal(String(selectedDays));
      } else {
        setIsCustomMode(false);
        if (selectedDays !== null) setCustomDaysVal(String(selectedDays));
      }
      setErrorMsg(null);
    }
  }, [isOpen, selectedDays]);

  useEffect(() => {
    if (isCustomMode && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isCustomMode]);

  const handleSelectPreset = (days: number | null, label: string) => {
    onApply(days, label);
    setIsOpen(false);
    setIsCustomMode(false);
  };

  const handleApplyCustom = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = customDaysVal.trim();
    const num = parseInt(trimmed, 10);

    if (isNaN(num) || num < 1) {
      setErrorMsg('Min 1 day');
      return;
    }
    if (num > 730) {
      setErrorMsg('Max 730 days');
      return;
    }

    setErrorMsg(null);
    onApply(num, `Last ${num} days`);
    setIsOpen(false);
    setIsCustomMode(false);
  };

  const displayLabel =
    activeLabel ||
    (selectedDays === null
      ? 'All time'
      : `Last ${selectedDays} day${selectedDays === 1 ? '' : 's'}`);

  const isCustomActive =
    selectedDays !== null && !PRESETS.some((p) => p.days === selectedDays);

  return (
    <div ref={containerRef} style={{ position: 'relative', display: 'inline-block' }}>
      {/* Trigger Button - Clean Minimalist Pill */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          padding: '6px 12px',
          borderRadius: 6,
          border: isOpen ? '1px solid #0A0A0A' : '1px solid #E2E8F0',
          background: '#FFFFFF',
          color: '#0F172A',
          fontSize: 13,
          fontWeight: 500,
          cursor: 'pointer',
          outline: 'none',
          boxShadow: isOpen
            ? '0 0 0 2px rgba(10, 10, 10, 0.08)'
            : '0 1px 2px rgba(0, 0, 0, 0.04)',
          transition: 'all 0.12s ease',
          userSelect: 'none',
        }}
        onMouseEnter={(e) => {
          if (!isOpen) e.currentTarget.style.borderColor = '#CBD5E1';
        }}
        onMouseLeave={(e) => {
          if (!isOpen) e.currentTarget.style.borderColor = '#E2E8F0';
        }}
      >
        <Calendar size={14} color="#64748B" />
        <span style={{ fontWeight: 600 }}>{displayLabel}</span>
        {isCustomActive && (
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              padding: '1px 5px',
              borderRadius: 4,
              background: '#FFF7ED',
              color: '#EA580C',
              border: '1px solid #FFEDD5',
            }}
          >
            Custom
          </span>
        )}
        <ChevronDown
          size={13}
          color="#94A3B8"
          style={{
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.15s ease',
            marginLeft: 2,
          }}
        />
      </button>

      {/* Dropdown Menu - Linear / Vercel style */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 5px)',
            right: 0,
            width: 230,
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: 8,
            boxShadow:
              '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.06)',
            zIndex: 9999,
            padding: '4px',
            animation: 'fadeInScale 0.1s ease-out',
            userSelect: 'none',
          }}
        >
          {/* Section Header */}
          <div
            style={{
              padding: '6px 8px 4px',
              fontSize: 11,
              fontWeight: 600,
              color: '#94A3B8',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Timeframe
          </div>

          {/* Preset Options */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {PRESETS.map((p) => {
              const isSelected = selectedDays === p.days;
              return (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => handleSelectPreset(p.days, p.label)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    padding: '7px 8px',
                    borderRadius: 5,
                    border: 'none',
                    background: isSelected ? '#F1F5F9' : 'transparent',
                    color: isSelected ? '#0F172A' : '#334155',
                    fontSize: 13,
                    fontWeight: isSelected ? 600 : 400,
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'background 0.1s ease',
                    outline: 'none',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.background = '#F8FAFC';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <span style={{ background: 'transparent' }}>{p.label}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span
                      style={{
                        fontSize: 11,
                        color: '#94A3B8',
                        fontWeight: 500,
                      }}
                    >
                      {p.badge}
                    </span>
                    {isSelected && (
                      <Check size={14} color="#0F172A" strokeWidth={2.5} />
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Separator */}
          <div style={{ height: 1, background: '#F1F5F9', margin: '4px 0' }} />

          {/* Custom Days Trigger / Inline Editor */}
          {!isCustomMode ? (
            <button
              type="button"
              onClick={() => setIsCustomMode(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                width: '100%',
                padding: '7px 8px',
                borderRadius: 5,
                border: 'none',
                background: isCustomActive ? '#FFF7ED' : 'transparent',
                color: isCustomActive ? '#C2410C' : '#334155',
                fontSize: 13,
                fontWeight: isCustomActive ? 600 : 400,
                cursor: 'pointer',
                textAlign: 'left',
                outline: 'none',
              }}
              onMouseEnter={(e) => {
                if (!isCustomActive) e.currentTarget.style.background = '#F8FAFC';
              }}
              onMouseLeave={(e) => {
                if (!isCustomActive) e.currentTarget.style.background = 'transparent';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <SlidersHorizontal size={13} color={isCustomActive ? '#EA580C' : '#64748B'} />
                <span>Custom days...</span>
              </div>
              {isCustomActive && (
                <span style={{ fontSize: 11, fontWeight: 700, color: '#EA580C' }}>
                  {selectedDays}d
                </span>
              )}
            </button>
          ) : (
            <form
              onSubmit={handleApplyCustom}
              style={{
                padding: '6px 8px',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
                background: '#F8FAFC',
                borderRadius: 6,
                marginTop: 2,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#475569' }}>
                  Past N Days
                </span>
                <button
                  type="button"
                  onClick={() => setIsCustomMode(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 0,
                    display: 'flex',
                    color: '#94A3B8',
                  }}
                >
                  <X size={13} />
                </button>
              </div>

              <div style={{ display: 'flex', gap: 4 }}>
                <div style={{ position: 'relative', flex: 1 }}>
                  <input
                    ref={inputRef}
                    type="number"
                    min="1"
                    max="730"
                    placeholder="Days (e.g. 45)"
                    value={customDaysVal}
                    onChange={(e) => {
                      setCustomDaysVal(e.target.value);
                      setErrorMsg(null);
                    }}
                    style={{
                      width: '100%',
                      padding: '5px 8px',
                      fontSize: 13,
                      borderRadius: 4,
                      border: errorMsg ? '1px solid #EF4444' : '1px solid #CBD5E1',
                      outline: 'none',
                      boxSizing: 'border-box',
                      fontWeight: 600,
                      color: '#0F172A',
                      background: '#FFFFFF',
                    }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    padding: '5px 10px',
                    fontSize: 12,
                    fontWeight: 600,
                    borderRadius: 4,
                    border: 'none',
                    background: '#0A0A0A',
                    color: '#FFFFFF',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 3,
                  }}
                >
                  <span>Apply</span>
                  <ArrowRight size={11} />
                </button>
              </div>

              {errorMsg && (
                <span style={{ fontSize: 10.5, color: '#DC2626', fontWeight: 500 }}>
                  {errorMsg}
                </span>
              )}
            </form>
          )}

          {/* Reset to Default Action if not on 30d */}
          {selectedDays !== 30 && selectedDays !== null && (
            <>
              <div style={{ height: 1, background: '#F1F5F9', margin: '4px 0' }} />
              <button
                type="button"
                onClick={() => handleSelectPreset(30, 'Last 30 days')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  width: '100%',
                  padding: '5px 8px',
                  borderRadius: 5,
                  border: 'none',
                  background: 'transparent',
                  color: '#64748B',
                  fontSize: 11.5,
                  fontWeight: 500,
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#0F172A')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#64748B')}
              >
                <RotateCcw size={11} />
                <span>Reset to default (30d)</span>
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};
