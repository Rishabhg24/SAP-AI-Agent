import { useState, useEffect, useRef, useCallback } from 'react';

// Browser SpeechRecognition Type Declarations
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

interface ISpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives?: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onstart: ((this: ISpeechRecognition, ev: Event) => any) | null;
  onend: ((this: ISpeechRecognition, ev: Event) => any) | null;
  onerror: ((this: ISpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
  onresult: ((this: ISpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
}

export interface UseVoiceInputOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  autoStopTimeoutMs?: number;
  onTranscriptChange?: (text: string, isFinal: boolean) => void;
  onFinalTranscript?: (text: string) => void;
  onError?: (error: string) => void;
}

export interface UseVoiceInputReturn {
  isListening: boolean;
  isSupported: boolean;
  audioLevel: number; // 0 to 100 for live waveform visualization
  transcript: string;
  interimTranscript: string;
  finalTranscript: string;
  error: string | null;
  language: string;
  setLanguage: (lang: string) => void;
  startListening: () => void;
  stopListening: () => void;
  toggleListening: () => void;
  resetTranscript: () => void;
  supportedLanguages: { code: string; label: string }[];
}

export const SUPPORTED_LANGUAGES = [
  { code: 'en-IN', label: 'English (India)' },
  { code: 'en-US', label: 'English (US)' },
  { code: 'en-GB', label: 'English (UK)' },
  { code: 'hi-IN', label: 'Hindi (India)' },
  { code: 'de-DE', label: 'German (SAP Standard)' },
];

export const useVoiceInput = (options: UseVoiceInputOptions = {}): UseVoiceInputReturn => {
  const {
    language: initialLanguage = 'en-IN',
    continuous = true,
    interimResults = true,
    autoStopTimeoutMs = 3000,
    onTranscriptChange,
    onFinalTranscript,
    onError,
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState(initialLanguage);
  const [audioLevel, setAudioLevel] = useState(0);

  // References for Web Speech Recognition and Web Audio API
  const recognitionRef = useRef<ISpeechRecognition | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isStoppingIntentionallyRef = useRef(false);

  // Check Web Speech API availability
  const isSupported =
    typeof window !== 'undefined' &&
    Boolean((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);

  // Clean up Audio Visualizer
  const cleanupAudioAnalyser = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try {
        audioContextRef.current.close();
      } catch (e) {
        // ignore
      }
      audioContextRef.current = null;
    }
    analyserRef.current = null;
    setAudioLevel(0);
  }, []);

  // Initialize Web Audio Analyzer for reactive sound waves
  const initAudioAnalyser = useCallback(async () => {
    try {
      if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      mediaStreamRef.current = stream;

      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContextClass) return;

      const audioCtx = new AudioContextClass();
      audioContextRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.5;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateVolume = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const avg = sum / bufferLength;
        // Normalize to 0 - 100 range with sensitivity scale
        const normalized = Math.min(100, Math.round((avg / 128) * 100));
        setAudioLevel(normalized);

        animFrameRef.current = requestAnimationFrame(updateVolume);
      };

      updateVolume();
    } catch (e) {
      // Audio visualizer fallback: speech recognition continues even if audio level fails
      console.warn('Audio level visualizer could not be initialized:', e);
    }
  }, []);

  // Reset silence auto-stop timer
  const resetSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (autoStopTimeoutMs > 0 && isListening) {
      silenceTimerRef.current = setTimeout(() => {
        // Auto-stop after silence threshold when speech has been received
        if (recognitionRef.current) {
          try {
            recognitionRef.current.stop();
          } catch (e) {
            // ignore
          }
        }
      }, autoStopTimeoutMs);
    }
  }, [autoStopTimeoutMs, isListening]);

  // Clean stop of Speech Recognition
  const stopListening = useCallback(() => {
    isStoppingIntentionallyRef.current = true;
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    cleanupAudioAnalyser();
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        // ignore
      }
    }
    setIsListening(false);
  }, [cleanupAudioAnalyser]);

  // Start Speech Recognition
  const startListening = useCallback(() => {
    if (!isSupported) {
      const errMsg = 'Voice Input is not supported in this browser. Please use Google Chrome, Edge, or Safari.';
      setError(errMsg);
      if (onError) onError(errMsg);
      return;
    }

    // Clean previous session if running
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {
        // ignore
      }
    }
    cleanupAudioAnalyser();

    setError(null);
    setInterimTranscript('');
    isStoppingIntentionallyRef.current = false;

    try {
      const SpeechRecognitionClass =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition: ISpeechRecognition = new SpeechRecognitionClass();

      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.lang = language;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
        setError(null);
        initAudioAnalyser();
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let currentInterim = '';
        let currentFinal = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const item = event.results[i];
          const text = item[0]?.transcript || '';

          if (item.isFinal) {
            currentFinal += text + ' ';
          } else {
            currentInterim += text;
          }
        }

        const trimmedFinal = currentFinal.trim();
        const trimmedInterim = currentInterim.trim();

        if (trimmedFinal) {
          setFinalTranscript((prev) => {
            const updated = prev ? `${prev} ${trimmedFinal}` : trimmedFinal;
            setTranscript(updated);
            if (onFinalTranscript) onFinalTranscript(updated);
            return updated;
          });
        }

        setInterimTranscript(trimmedInterim);

        const liveCombined = (
          (finalTranscript ? finalTranscript + ' ' : '') +
          (trimmedFinal ? trimmedFinal + ' ' : '') +
          trimmedInterim
        ).trim();

        if (onTranscriptChange && liveCombined) {
          onTranscriptChange(liveCombined, Boolean(trimmedFinal && !trimmedInterim));
        }

        // Reset silence timer on every speech event
        resetSilenceTimer();
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        let errMessage = 'Voice input error occurred.';
        switch (event.error) {
          case 'not-allowed':
          case 'permission-denied':
            errMessage = 'Microphone access was denied. Please allow microphone permissions in your browser.';
            break;
          case 'no-speech':
            // Non-critical: user was quiet
            return;
          case 'audio-capture':
            errMessage = 'No microphone was found on this system.';
            break;
          case 'network':
            errMessage = 'Network communication issue with speech recognition service.';
            break;
          case 'aborted':
            return;
          default:
            errMessage = `Speech recognition error: ${event.error}`;
        }
        setError(errMessage);
        if (onError) onError(errMessage);
        stopListening();
      };

      recognition.onend = () => {
        // If not intentionally stopped and still continuous, restart or finish
        setIsListening(false);
        cleanupAudioAnalyser();
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      const errMsg = err?.message || 'Failed to start microphone speech recognition.';
      setError(errMsg);
      if (onError) onError(errMsg);
      setIsListening(false);
      cleanupAudioAnalyser();
    }
  }, [
    isSupported,
    continuous,
    interimResults,
    language,
    finalTranscript,
    cleanupAudioAnalyser,
    initAudioAnalyser,
    resetSilenceTimer,
    onTranscriptChange,
    onFinalTranscript,
    onError,
    stopListening,
  ]);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setFinalTranscript('');
    setError(null);
  }, []);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {
          // ignore
        }
      }
      cleanupAudioAnalyser();
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
    };
  }, [cleanupAudioAnalyser]);

  return {
    isListening,
    isSupported,
    audioLevel,
    transcript,
    interimTranscript,
    finalTranscript,
    error,
    language,
    setLanguage,
    startListening,
    stopListening,
    toggleListening,
    resetTranscript,
    supportedLanguages: SUPPORTED_LANGUAGES,
  };
};
