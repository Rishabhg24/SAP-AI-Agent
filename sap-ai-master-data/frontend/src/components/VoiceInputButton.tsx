import React, { useState, useEffect } from 'react';
import { Mic, MicOff, AlertCircle, Globe, ChevronDown, Check, Send, X, Sparkles } from 'lucide-react';
import { useVoiceInput } from '../hooks/useVoiceInput';
import '../styles/voice-input.css';

export interface VoiceInputButtonProps {
  onTranscript: (text: string, isFinal: boolean) => void;
  onSendDirectly?: (text: string) => void;
  disabled?: boolean;
  autoSendEnabled?: boolean;
  onAutoSendToggle?: (enabled: boolean) => void;
  className?: string;
  showLanguageSelector?: boolean;
  showVisualizerBanner?: boolean;
  variant?: 'default' | 'vocalyn';
  activeLanguage?: string;
  onLanguageChange?: (lang: string) => void;
}

export const VoiceInputButton: React.FC<VoiceInputButtonProps> = ({
  onTranscript,
  onSendDirectly,
  disabled = false,
  autoSendEnabled = false,
  onAutoSendToggle,
  className = '',
  showLanguageSelector = true,
  showVisualizerBanner = true,
  variant = 'default',
  activeLanguage,
  onLanguageChange,
}) => {
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [activeSpeechText, setActiveSpeechText] = useState('');

  const {
    isListening,
    isSupported,
    audioLevel,
    interimTranscript,
    finalTranscript,
    error,
    language,
    setLanguage,
    toggleListening,
    stopListening,
    resetTranscript,
    supportedLanguages,
  } = useVoiceInput({
    language: activeLanguage || 'en-IN',
    onTranscriptChange: (text, isFinal) => {
      setActiveSpeechText(text);
      onTranscript(text, isFinal);
    },
    onFinalTranscript: (text) => {
      setActiveSpeechText(text);
      if (autoSendEnabled && onSendDirectly && text.trim()) {
        onSendDirectly(text.trim());
        stopListening();
        resetTranscript();
        setActiveSpeechText('');
      }
    },
  });

  useEffect(() => {
    if (activeLanguage && activeLanguage !== language) {
      setLanguage(activeLanguage);
    }
  }, [activeLanguage, language, setLanguage]);

  // Global keyboard shortcut: Alt + V to toggle voice recognition
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === 'v' || e.key === 'V')) {
        e.preventDefault();
        if (!disabled && isSupported) {
          toggleListening();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [disabled, isSupported, toggleListening]);

  // Handle Escape / Enter when listening overlay is active
  useEffect(() => {
    if (!isListening) return;
    const handleOverlayKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        stopListening();
        resetTranscript();
        setActiveSpeechText('');
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const textToSubmit = (activeSpeechText || finalTranscript || interimTranscript).trim();
        if (textToSubmit && onSendDirectly) {
          onSendDirectly(textToSubmit);
        }
        stopListening();
        resetTranscript();
        setActiveSpeechText('');
      }
    };
    window.addEventListener('keydown', handleOverlayKey);
    return () => window.removeEventListener('keydown', handleOverlayKey);
  }, [isListening, activeSpeechText, finalTranscript, interimTranscript, onSendDirectly, stopListening, resetTranscript]);

  // Close language menu on outside click
  useEffect(() => {
    if (!showLangMenu) return;
    const handleClickOutside = () => setShowLangMenu(false);
    window.addEventListener('click', handleClickOutside);
    return () => window.removeEventListener('click', handleClickOutside);
  }, [showLangMenu]);

  // Fallback for unsupported browsers
  if (!isSupported) {
    return (
      <button
        type="button"
        disabled
        className="voice-btn-disabled"
        title="Voice Input is not supported by your browser. Please use Chrome, Edge, or Safari."
      >
        <MicOff size={16} />
      </button>
    );
  }

  const currentLangLabel =
    supportedLanguages.find((l) => l.code === language)?.label || 'English';

  const handleFinishAndSubmit = () => {
    const textToSubmit = (activeSpeechText || finalTranscript || interimTranscript).trim();
    if (textToSubmit && onSendDirectly) {
      onSendDirectly(textToSubmit);
    }
    stopListening();
    resetTranscript();
    setActiveSpeechText('');
  };

  const handleCancelOverlay = () => {
    stopListening();
    resetTranscript();
    setActiveSpeechText('');
  };

  // Calculate dynamic ring scale based on live volume
  const dynamicScale = 1 + (audioLevel / 100) * 0.25;

  return (
    <div className={`voice-input-container ${className}`}>
      {/* ==========================================================
          IMMERSIVE VOICE ASSISTANT LISTENING OVERLAY
          ========================================================== */}
      {showVisualizerBanner && isListening && (
        <div className="voice-listening-overlay" onClick={handleCancelOverlay}>
          <div className="voice-listening-overlay-card" onClick={(e) => e.stopPropagation()}>
            {/* Top Bar */}
            <div className="voice-overlay-topbar">
              <div className="voice-overlay-badge">
                <Sparkles size={14} color="#60A5FA" />
                <span>Hey CIRA • Voice Assistant</span>
              </div>

              <div className="voice-overlay-top-actions">
                <div className="voice-overlay-lang-wrapper" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={() => setShowLangMenu(!showLangMenu)}
                    className="voice-overlay-lang-btn"
                    title="Change recognition dialect"
                  >
                    <Globe size={13} />
                    <span>{currentLangLabel}</span>
                    <ChevronDown size={12} />
                  </button>

                  {showLangMenu && (
                    <div className="voice-lang-menu-dropdown overlay-dropdown">
                      <div className="voice-lang-menu-header">Recognition Dialect</div>
                      {supportedLanguages.map((langItem) => (
                        <button
                          key={langItem.code}
                          type="button"
                          onClick={() => {
                            setLanguage(langItem.code);
                            if (onLanguageChange) onLanguageChange(langItem.code);
                            setShowLangMenu(false);
                          }}
                          className={`voice-lang-menu-item ${
                            language === langItem.code ? 'active' : ''
                          }`}
                        >
                          <span>{langItem.label}</span>
                          {language === langItem.code && <Check size={13} color="#1A56DB" />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={handleCancelOverlay}
                  className="voice-overlay-close-btn"
                  title="Close (Esc)"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Central Ripple Rings + White Microphone Circle */}
            <div className="voice-ripple-stage" onClick={handleFinishAndSubmit} title="Click to stop and submit">
              {/* Outer Ripple Ring 3 */}
              <div
                className="voice-ripple-ring voice-ripple-ring-3"
                style={{ transform: `scale(${dynamicScale * 1.15})` }}
              />

              {/* Middle Ripple Ring 2 */}
              <div
                className="voice-ripple-ring voice-ripple-ring-2"
                style={{ transform: `scale(${dynamicScale * 1.08})` }}
              />

              {/* Inner Ripple Ring 1 */}
              <div
                className="voice-ripple-ring voice-ripple-ring-1"
                style={{ transform: `scale(${dynamicScale})` }}
              />

              {/* Center White Microphone Circle Button */}
              <div className="voice-center-white-orb">
                <Mic size={38} color="#000000" strokeWidth={2.2} />
              </div>
            </div>

            {/* "Listening..." Title */}
            <div className="voice-listening-title">Listening...</div>

            {/* Real-time speech transcript output */}
            <div className="voice-overlay-transcript-area">
              {activeSpeechText || interimTranscript || finalTranscript ? (
                <div className="voice-overlay-live-text">
                  <span className="voice-overlay-final-text">{finalTranscript}</span>
                  {interimTranscript && (
                    <span className="voice-overlay-interim-text"> {interimTranscript}</span>
                  )}
                </div>
              ) : (
                <div className="voice-overlay-placeholder-text">
                  Say: "Show all active items", "Find missing HSN", "Create customer Apex Global"...
                </div>
              )}
            </div>

            {/* Bottom Actions Bar */}
            <div className="voice-overlay-footer">
              <div className="voice-overlay-footer-left">
                {onAutoSendToggle && (
                  <button
                    type="button"
                    onClick={() => onAutoSendToggle(!autoSendEnabled)}
                    className={`voice-autosend-toggle ${autoSendEnabled ? 'active' : ''}`}
                    title={
                      autoSendEnabled
                        ? 'Auto-Send enabled: prompt sends automatically after speaking'
                        : 'Review first: prompt fills into input for review'
                    }
                  >
                    <span>{autoSendEnabled ? '⚡ Auto-Send: ON' : '✍️ Review First'}</span>
                  </button>
                )}
              </div>

              <div className="voice-overlay-footer-right">
                <button
                  type="button"
                  onClick={handleCancelOverlay}
                  className="voice-overlay-cancel-btn"
                >
                  Cancel
                </button>

                {(activeSpeechText || finalTranscript || interimTranscript) && (
                  <button
                    type="button"
                    onClick={handleFinishAndSubmit}
                    className="voice-overlay-submit-btn"
                  >
                    <Send size={13} />
                    <span>Send to Hey CIRA</span>
                  </button>
                )}
              </div>
            </div>

            <div className="voice-overlay-hint-text">
              Click center circle or press <kbd>Enter</kbd> to send • Press <kbd>Esc</kbd> to cancel
            </div>
          </div>
        </div>
      )}

      {/* Error Alert Pill if permission denied or error occurs */}
      {error && (
        <div className="voice-error-pill" role="alert">
          <AlertCircle size={14} />
          <span>{error}</span>
          <button
            type="button"
            onClick={resetTranscript}
            className="voice-error-dismiss"
            title="Dismiss error"
          >
            <X size={12} />
          </button>
        </div>
      )}

      {/* Main Mic Button & Controls Group */}
      <div className="voice-btn-group">
        {/* Language selector toggle */}
        {showLanguageSelector && (
          <div className="voice-lang-selector-wrapper" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              disabled={disabled || isListening}
              onClick={() => setShowLangMenu(!showLangMenu)}
              className="voice-lang-chip-btn"
              title={`Speech Language: ${currentLangLabel} (Click to change)`}
            >
              <Globe size={13} />
              <span>{language.toUpperCase()}</span>
              <ChevronDown size={11} />
            </button>

            {showLangMenu && (
              <div className="voice-lang-menu-dropdown">
                <div className="voice-lang-menu-header">Recognition Dialect</div>
                {supportedLanguages.map((langItem) => (
                  <button
                    key={langItem.code}
                    type="button"
                    onClick={() => {
                      setLanguage(langItem.code);
                      if (onLanguageChange) onLanguageChange(langItem.code);
                      setShowLangMenu(false);
                    }}
                    className={`voice-lang-menu-item ${
                      language === langItem.code ? 'active' : ''
                    }`}
                  >
                    <span>{langItem.label}</span>
                    {language === langItem.code && <Check size={13} color="#1A56DB" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Voice Mic Button */}
        {variant === 'vocalyn' ? (
          <button
            type="button"
            onClick={toggleListening}
            disabled={disabled}
            className={`vocalyn-mic-circle-btn ${isListening ? 'listening' : ''}`}
            title={
              isListening
                ? 'Listening... Click to stop voice input (Alt + V)'
                : 'Click to speak (Alt + V)'
            }
          >
            {isListening ? (
              <MicOff size={19} color="#DC2626" />
            ) : (
              <Mic size={19} />
            )}
          </button>
        ) : (
          <button
            type="button"
            onClick={toggleListening}
            disabled={disabled}
            className={`voice-mic-main-btn ${isListening ? 'listening' : ''}`}
            title={
              isListening
                ? 'Listening... Click to stop voice input (Alt + V)'
                : 'Voice Input: Click to speak your prompt to Hey CIRA (Alt + V)'
            }
          >
            {isListening ? (
              <>
                <span className="voice-active-radar" />
                <MicOff size={16} className="voice-mic-icon-active" />
                <span className="voice-listening-label">Stop</span>
              </>
            ) : (
              <>
                <Mic size={16} className="voice-mic-icon" />
                <span className="voice-btn-text">Voice</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export default VoiceInputButton;
