#!/usr/bin/env python3
"""
Latency measurement script for FlexiAI assistant pipeline.

This script helps measure the latency breakdown in the assistant request
processing to identify optimization opportunities, particularly around
file I/O operations that could be eliminated with streaming approaches.

Usage:
    python measure_latency.py [--runs N] [--duration SECONDS] [--synthetic]
"""

import argparse
import time
import tempfile
import os
import statistics
from typing import List, Dict
import numpy as np

# Try to import FlexiAI components
try:
    from flexiai.models import ModelFactory, ModelType
    from flexiai.audio import AudioUtils, AudioRecorder
    from flexiai.utils import debug_print
    FLEXIAI_AVAILABLE = True
except ImportError:
    print("❌ FlexiAI not available. Install with: pip install -e .")
    FLEXIAI_AVAILABLE = False


class LatencyProfiler:
    """Profiles latency in the FlexiAI assistant pipeline."""

    def __init__(self, device: str = "auto"):
        self.device = self._determine_device(device)
        self.assistant_model = None
        self.results = []

    def _determine_device(self, device: str) -> str:
        """Determine the best device to use."""
        if device == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return device

    def setup_models(self, model_name: str = "mistralai/Voxtral-Mini-3B-2507 ") -> bool:
        """Initialize the assistant model for testing."""
        print(f"🚀 Loading assistant model: {model_name}")
        print(f"📱 Using device: {self.device}")

        self.assistant_model = ModelFactory.create_assistant_model(
            model_name,
            self.device
        )

        if not self.assistant_model:
            print(f"❌ Failed to create model: {model_name}")
            return False

        if not self.assistant_model.load():
            print(f"❌ Failed to load model: {model_name}")
            return False

        print(f"✅ Model loaded successfully")
        return True

    def generate_synthetic_audio(self, duration: float = 2.0, sample_rate: int = 16000) -> List[bytes]:
        """Generate synthetic audio frames for testing."""
        print(f"🎵 Generating {duration}s of synthetic audio...")

        # Generate a simple sine wave
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)

        # Mix of frequencies to simulate speech
        frequency1 = 440  # A4 note
        frequency2 = 880  # A5 note
        audio = 0.3 * (np.sin(frequency1 * 2 * np.pi * t) +
                      0.5 * np.sin(frequency2 * 2 * np.pi * t))

        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)

        # Split into frames (30ms chunks for VAD compatibility)
        frame_size = int(sample_rate * 0.030)  # 30ms frames
        frames = []

        for i in range(0, len(audio_int16), frame_size):
            frame = audio_int16[i:i+frame_size]
            if len(frame) == frame_size:  # Only include complete frames
                frames.append(frame.tobytes())

        print(f"✅ Generated {len(frames)} audio frames")
        return frames

    def record_real_audio(self, duration: float = 3.0) -> List[bytes]:
        """Record real audio for testing."""
        print(f"🎤 Recording {duration}s of real audio...")
        print("   Say something for the assistant to process...")

        recorder = AudioRecorder()

        if not recorder.start_recording():
            raise RuntimeError("Failed to start audio recording")

        time.sleep(duration)
        frames, stats = recorder.stop_recording()

        print(f"✅ Recorded {len(frames)} frames ({stats.get('duration_seconds', 0):.1f}s)")
        return frames

    def measure_file_operations(self, frames: List[bytes], runs: int = 5) -> Dict:
        """Measure file I/O operations separately."""
        print(f"📁 Measuring file operations ({runs} runs)...")

        creation_times = []
        cleanup_times = []
        file_sizes = []

        for run in range(runs):
            # Measure file creation
            start_time = time.time()
            temp_file = AudioUtils.create_temp_wav_file(frames, 16000)
            creation_time = time.time() - start_time
            creation_times.append(creation_time)

            if temp_file:
                # Measure file size
                file_size = os.path.getsize(temp_file)
                file_sizes.append(file_size)

                # Measure cleanup
                start_time = time.time()
                os.unlink(temp_file)
                cleanup_time = time.time() - start_time
                cleanup_times.append(cleanup_time)

        return {
            'creation_mean': statistics.mean(creation_times) * 1000,
            'creation_stdev': statistics.stdev(creation_times) * 1000 if len(creation_times) > 1 else 0,
            'cleanup_mean': statistics.mean(cleanup_times) * 1000,
            'cleanup_stdev': statistics.stdev(cleanup_times) * 1000 if len(cleanup_times) > 1 else 0,
            'file_size_mean': statistics.mean(file_sizes),
            'total_file_overhead': statistics.mean([c + cl for c, cl in zip(creation_times, cleanup_times)]) * 1000
        }

    def measure_inference_pipeline(self, frames: List[bytes], runs: int = 3) -> Dict:
        """Measure the complete inference pipeline."""
        print(f"🧠 Measuring inference pipeline ({runs} runs)...")

        if not self.assistant_model:
            raise RuntimeError("Assistant model not loaded")

        total_times = []
        inference_times = []

        for run in range(runs):
            print(f"   Run {run + 1}/{runs}")

            # Measure total pipeline time
            total_start = time.time()

            # Create temp file (this will be measured internally)
            temp_file = AudioUtils.create_temp_wav_file(frames, 16000)

            if not temp_file:
                raise RuntimeError("Failed to create temp file")

            try:
                # Measure inference only
                inference_start = time.time()
                response = self.assistant_model.generate_response(
                    temp_file,
                    prompt="Please provide a brief response to test latency."
                )
                inference_time = time.time() - inference_start
                inference_times.append(inference_time)

                total_time = time.time() - total_start
                total_times.append(total_time)

                print(f"     Response length: {len(response)} chars")

            finally:
                os.unlink(temp_file)

        return {
            'total_mean': statistics.mean(total_times) * 1000,
            'total_stdev': statistics.stdev(total_times) * 1000 if len(total_times) > 1 else 0,
            'inference_mean': statistics.mean(inference_times) * 1000,
            'inference_stdev': statistics.stdev(inference_times) * 1000 if len(inference_times) > 1 else 0,
        }

    def run_comprehensive_test(self, audio_frames: List[bytes], runs: int = 3) -> Dict:
        """Run comprehensive latency measurements."""
        print("\n🔬 Running comprehensive latency analysis...")

        # Measure file operations
        file_results = self.measure_file_operations(audio_frames, runs * 2)

        # Measure inference pipeline
        inference_results = self.measure_inference_pipeline(audio_frames, runs)

        # Calculate potential savings
        file_overhead_pct = (file_results['total_file_overhead'] /
                           inference_results['total_mean']) * 100

        results = {
            'file_operations': file_results,
            'inference_pipeline': inference_results,
            'optimization_potential': {
                'file_overhead_ms': file_results['total_file_overhead'],
                'file_overhead_percentage': file_overhead_pct,
                'potential_speedup': f"{file_overhead_pct:.1f}% faster"
            }
        }

        self.results.append(results)
        return results

    def print_results(self, results: Dict):
        """Print formatted results."""
        print("\n" + "="*60)
        print("📊 LATENCY ANALYSIS RESULTS")
        print("="*60)

        file_ops = results['file_operations']
        inference = results['inference_pipeline']
        optimization = results['optimization_potential']

        print(f"\n📁 File Operations:")
        print(f"   • Creation:     {file_ops['creation_mean']:5.1f}ms ± {file_ops['creation_stdev']:4.1f}ms")
        print(f"   • Cleanup:      {file_ops['cleanup_mean']:5.1f}ms ± {file_ops['cleanup_stdev']:4.1f}ms")
        print(f"   • File size:    {file_ops['file_size_mean']/1024:5.1f}KB")
        print(f"   • Total overhead: {file_ops['total_file_overhead']:5.1f}ms")

        print(f"\n🧠 Inference Pipeline:")
        print(f"   • Total time:   {inference['total_mean']:5.1f}ms ± {inference['total_stdev']:4.1f}ms")
        print(f"   • Inference only: {inference['inference_mean']:5.1f}ms ± {inference['inference_stdev']:4.1f}ms")

        print(f"\n🎯 Optimization Potential:")
        print(f"   • File overhead: {optimization['file_overhead_ms']:5.1f}ms ({optimization['file_overhead_percentage']:4.1f}% of total)")
        print(f"   • Potential gain: {optimization['potential_speedup']}")

        # Recommendation
        if optimization['file_overhead_percentage'] > 10:
            print(f"\n✅ RECOMMENDATION: High optimization potential!")
            print(f"   File I/O represents {optimization['file_overhead_percentage']:.1f}% of total latency.")
            print(f"   Streaming optimization is likely worth the engineering effort.")
        elif optimization['file_overhead_percentage'] > 5:
            print(f"\n⚠️  RECOMMENDATION: Moderate optimization potential.")
            print(f"   File I/O represents {optimization['file_overhead_percentage']:.1f}% of total latency.")
            print(f"   Consider optimization if latency is critical.")
        else:
            print(f"\n❌ RECOMMENDATION: Low optimization potential.")
            print(f"   File I/O represents only {optimization['file_overhead_percentage']:.1f}% of total latency.")
            print(f"   Engineering effort may not be justified.")


def main():
    parser = argparse.ArgumentParser(description="Measure FlexiAI assistant latency")
    parser.add_argument("--runs", type=int, default=3, help="Number of test runs")
    parser.add_argument("--duration", type=float, default=2.0, help="Audio duration in seconds")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic audio instead of recording")
    parser.add_argument("--device", default="auto", help="Device to use (auto, cpu, cuda)")
    parser.add_argument("--model", default="mistralai/Voxtral-Mini-3B-2507", help="Model to test")

    args = parser.parse_args()

    if not FLEXIAI_AVAILABLE:
        return 1

    print("🔬 FlexiAI Latency Measurement Tool")
    print("="*50)

    # Initialize profiler
    profiler = LatencyProfiler(args.device)

    # Setup models
    if not profiler.setup_models(args.model):
        return 1

    try:
        # Get audio data
        if args.synthetic:
            frames = profiler.generate_synthetic_audio(args.duration)
        else:
            frames = profiler.record_real_audio(args.duration)

        if not frames:
            print("❌ No audio data available")
            return 1

        # Run measurements
        results = profiler.run_comprehensive_test(frames, args.runs)

        # Display results
        profiler.print_results(results)

        print(f"\n🏁 Analysis complete!")

    except KeyboardInterrupt:
        print("\n⏹️  Measurement interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during measurement: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
