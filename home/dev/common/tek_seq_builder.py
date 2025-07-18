# Author: feihoo87  <xuhk@baqis.ac.cn>  2021/01/01

import datetime as dt
import hashlib
import io
import time
import zipfile
from collections import defaultdict
from functools import lru_cache

import numpy as np


def timestampString() -> str:
    """form the timestamp string"""

    timezone = time.timezone
    tz_m, _ = divmod(timezone, 60)  # returns (minutes, seconds)
    tz_h, tz_m = divmod(tz_m, 60)
    if np.sign(tz_h) == -1:
        signstr = '-'
        tz_h *= -1
    else:
        signstr = '+'
    timestr = dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    timestr += signstr
    timestr += '{:02.0f}:{:02.0f}'.format(tz_h, tz_m)
    return timestr


# 根据 Delft 的代码注释描述，使用各类 xml 解析库来生成 xml 文件会耗费大量时间，
# 那样做尽管使代码看起来好像更专业，但是实际上会使生成 wfmx 文件的时间增加 10 倍以上。
# 因此这里直接用格式化字符串的方式来生成所有的 xml。

WFMXFileHeaderTemplate = """<DataFile offset="{offset}" version="0.2">
  <DataSetsCollection xmlns="http://www.tektronix.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.tektronix.com file:///C:\\Program%20Files\\Tektronix\\AWG5200\AWG\Schemas\\awgDataSets.xsd">
    <DataSets version="1" xmlns="http://www.tektronix.com">
      <DataDescription>
        <NumberSamples>{num_samples}</NumberSamples>
        <SamplesType>AWGWaveformSample</SamplesType>
        <MarkersIncluded>{markers_included}</MarkersIncluded>
        <NumberFormat>Single</NumberFormat>
        <Endian>Little</Endian>
        <Timestamp>{timestamp}</Timestamp>
      </DataDescription>
      <ProductSpecific name="">
        <RecSamplingRate units="Hz">NaN</RecSamplingRate>
        <RecAmplitude units="Volts">NaN</RecAmplitude>
        <RecOffset units="Volts">NaN</RecOffset>
        <RecFrequency units="Hz">NaN</RecFrequency>
        <SerialNumber />
        <SoftwareVersion>6.3.0084.0</SoftwareVersion>
        <UserNotes />
        <Thumbnail />
        <SignalFormat>Real</SignalFormat>
        <CreatorProperties name="" />
      </ProductSpecific>
    </DataSets>
  </DataSetsCollection>
  <Setup />
</DataFile>"""


def makeWFMXFileHeader(num_samples: int, markers_included: bool) -> str:
    """
    Compiles a valid XML header for a .wfmx file
    There might be behaviour we can't capture
    We always use 9 digits for the number of header character
    """
    header = WFMXFileHeaderTemplate.format(
        offset="000000000",
        num_samples=num_samples,
        markers_included=str(markers_included).lower(),
        timestamp=timestampString())

    return header.replace('offset="000000000"', 'offset="%09d"' % len(header))


def makeWFMXFileBinaryData(wfm: np.ndarray, markerData: np.ndarray) -> bytes:
    """
    For the binary part.
    Args:
        wfm: A shape (N,) array with a waveform. The waveform the waveform
            must be rescaled to (-1, 1).
        markers: 0 ~ 4 shape (N, ) array with dtype=np.uint8.
    """
    N = wfm.shape[0]

    wfm = (wfm * 2**15).astype(np.int16).astype(np.float32) / 2**15

    # default little-endian on x86 CPU and ARM CPU
    # 用 struct.pack 耗时将多 5 倍，但如果在非 x86 平台运行，可能要仔细考虑端序的问题
    binary_wfm = wfm.tobytes()

    if markerData is not None:
        binary_wfm += markerData.astype(np.uint8).tobytes()

    return binary_wfm


def _makeSMLFileStep(elem_names,
                     tracks,
                     index,
                     assetType,
                     wait='None',
                     goto='Next',
                     repeatCount=1,
                     jumpInput='None',
                     jumpTo='Next'):
    """
    Args:
        index: step number
        wait: 'None' | 'TrigA' | 'TrigB' | 'Internal'
        goto: 'Next' | int
        repeatCount: int, 0 for infinite
        jumpInput: 'None' | 'TrigA' | 'TrigB' | 'Internal'
        jumpTo: 'Next' | int
    """

    if repeatCount == 0:
        repeatCount = 1
        repeat = 'Infinite'
    elif repeatCount == 1:
        repeat = 'Once'
    else:
        repeat = 'RepeatCount'

    if goto == 'Next':
        gotoStep = 1
    else:
        gotoStep = goto
        goto = 'StepIndex'

    if jumpTo == 'Next':
        jumpToStep = 1
    else:
        jumpToStep = jumpTo
        jumpTo = 'StepIndex'

    #if len(elem_names) == tracks:
    #    assetType = 'Waveform'
    #else:
    #    assetType = 'Sequence'

    assetTemplate = """
              <Asset>
                <AssetName>{name}</AssetName>
                <AssetType>{assetType}</AssetType>
              </Asset>"""

    flagSetTemplate = """
              <FlagSet>
                <Flag name="A">NoChange</Flag>
                <Flag name="B">NoChange</Flag>
                <Flag name="C">NoChange</Flag>
                <Flag name="D">NoChange</Flag>
              </FlagSet>"""

    flags = []
    assets = []
    for i in range(tracks):
        flags.append(flagSetTemplate)
        if assetType == 'Sequence':
            assets.append(
                assetTemplate.format(name=elem_names[0], assetType=assetType))
        else:
            assets.append(
                assetTemplate.format(name=elem_names[i], assetType=assetType))

    assets = ''.join(assets)
    flags = ''.join(flags)

    return f"""
          <Step>
            <StepNumber>{index}</StepNumber>
            <Repeat>{repeat}</Repeat>
            <RepeatCount>{repeatCount}</RepeatCount>
            <WaitInput>{wait}</WaitInput>
            <EventJumpInput>{jumpInput}</EventJumpInput>
            <EventJumpTo>{jumpTo}</EventJumpTo>
            <EventJumpToStep>{jumpToStep}</EventJumpToStep>
            <GoTo>{goto}</GoTo>
            <GoToStep>{gotoStep}</GoToStep>
            <Assets>{assets}
            </Assets>
            <Flags>{flags}
            </Flags>
          </Step>"""


smlTemplate = """<DataFile offset="{offset}" version="0.1">
  <DataSetsCollection xmlns="http://www.tektronix.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.tektronix.com file:///C:\\Program%20Files\\Tektronix\\AWG5200\AWG\Schemas\\awgSeqDataSets.xsd">
    <DataSets version="1" xmlns="http://www.tektronix.com">
      <DataDescription>
        <SequenceName>{name}</SequenceName>
        <Timestamp>{timestamp}</Timestamp>
        <JumpTiming>JumpImmed</JumpTiming>
        <RecSampleRate>NaN</RecSampleRate>
        <RepeatFlag>false</RepeatFlag>
        <PatternJumpTable Enabled="false" Count="256" />
        <Steps StepCount="{stepCount}" TrackCount="{trackCount}">{steps}
        </Steps>
      </DataDescription>
      <ProductSpecific name="" />
    </DataSets>
  </DataSetsCollection>
  <Setup />
</DataFile>
"""


def _makeSMLFile(name: str, stepCount: int, trackCount: int,
                 steps: str) -> str:
    sml = smlTemplate.format(offset="000000000",
                             name=name,
                             steps=steps,
                             stepCount=stepCount,
                             trackCount=trackCount,
                             timestamp=timestampString())

    return sml.replace('offset="000000000"', 'offset="%09d"' % len(sml))


seqSetupTemplate = """<RSAPersist version="0.1">
  <Application>Pascal</Application>
  <MainSequence>{mainSequence}</MainSequence>
  <ProductSpecific name="AWG5208">
    <SerialNumber>B030506</SerialNumber>
    <SoftwareVersion>6.3.0084.0</SoftwareVersion>
    <CreatorProperties name="" />
  </ProductSpecific>
</RSAPersist>"""


def _makeSetupFile(sequence: str) -> str:
    """
    Make a setup.xml file.
    Args:
        sequence: The name of the main sequence
    Returns:
        The setup file as a string
    """
    return seqSetupTemplate.format(mainSequence=sequence)


class SequenceBuilder():
    minLen = 2500

    def __init__(self, name, tracks=8):
        self.name = name
        self.tracks = tracks
        self._waveforms = set()
        self._buff = io.BytesIO()
        self._zip = zipfile.ZipFile(self._buff, mode='a')
        self._zip.writestr('userNotes.txt', b'')
        self._zip.writestr('setup.xml',
                           _makeSetupFile(self.name).encode('ascii'))
        self._stepnum = 1
        self.steps = []
        self._built = False

    def __del__(self):
        try:
            self._zip.close()
            self._buff.close()
        finally:
            pass

    def waveformName(self, points, markerData):
        if markerData is None or not any(markerData):
            markerData = None
        if np.max(np.abs(points)) <= 1 / (2**16) and markerData is None:
            wfmx_data = makeWFMXFileBinaryData(np.zeros_like(points), None)
            waveform_name = f'Zeros{points.shape[0]}'
        else:
            wfmx_data = makeWFMXFileBinaryData(points, markerData)
            waveform_name = hashlib.md5(wfmx_data).hexdigest()
        if waveform_name not in self._waveforms:
            wfmx_header = makeWFMXFileHeader(
                num_samples=points.shape[0],
                markers_included=False if markerData is None else True)
            self._zip.writestr(f'Waveforms/{waveform_name}.wfmx',
                               wfmx_header.encode('ascii') + wfmx_data)
            self._waveforms.add(waveform_name)
        return waveform_name

    def addStep(self,
                waveforms,
                wait='None',
                goto='Next',
                repeatCount=1,
                jumpInput='None',
                jumpTo='Next',
                secondary_wait='None'):
        """Add a step of sequence
        
        Args:
            waveforms: list of waveforms for every tracks
            wait: 'None' | 'TrigA' | 'TrigB' | 'Internal'
            goto: 'Next' | int
            repeatCount: int, 0 for infinite
            jumpInput: 'None' | 'TrigA' | 'TrigB' | 'Internal'
            jumpTo: 'Next' | int
            secondary_wait: 'None' | 'TrigA' | 'TrigB' | 'Internal'
        """
        if self._built:
            raise RuntimeError('Sequence already built.')

        if len(waveforms) != self.tracks:
            raise ValueError('%d waveforms input, but %d required.' %
                             (len(waveforms), self.tracks))

        subName = self.makeSubSequence(
            *[self.sliceWaveform(waveform) for waveform in waveforms],
            wait=secondary_wait)
        self.steps.append(
            _makeSMLFileStep([subName], self.tracks, self._stepnum, 'Sequence',
                             wait, goto, repeatCount, jumpInput, jumpTo))
        self._stepnum += 1

    def makeSequence(self, path=None):
        if self._built:
            return
        stepCount = len(self.steps)
        steps = ''.join(self.steps)
        sml = _makeSMLFile(self.name, stepCount, self.tracks, steps)
        self._zip.writestr(f'Sequences/{self.name}.sml', sml.encode('ascii'))

        self._built = True

        if path is not None:
            from pathlib import Path
            fname = Path(path) / f'{self.name}.seqx'
            fname.parent.mkdir(parents=True, exist_ok=True)
            with open(fname, 'wb') as f:
                f.write(self.seqx())

    @lru_cache(maxsize=1)
    def seqx(self):
        self._zip.close()
        self._buff.seek(0)
        return self._buff.getvalue()

    def makeSubSequence(self, *tracks, wait='None'):
        steps = []
        current_waveforms, current_repeat = None, None
        for waveforms in zip(*tracks):
            if current_waveforms is None:
                current_waveforms, current_repeat = waveforms, 1
            elif current_waveforms == waveforms:
                current_repeat += 1
            else:
                steps.append((current_waveforms, current_repeat))
                current_waveforms, current_repeat = waveforms, 1
        steps.append((current_waveforms, current_repeat))
        stepCount = len(steps)
        steps = ''.join([
            _makeSMLFileStep(waveforms,
                             self.tracks,
                             index,
                             'Waveform',
                             wait=wait if index == 1 else 'None',
                             goto='Next',
                             repeatCount=repeatCount,
                             jumpInput='None',
                             jumpTo='Next')
            for index, (waveforms, repeatCount) in enumerate(steps, start=1)
        ])
        name = f"Step{self._stepnum}Of{self.name}"
        sml = _makeSMLFile(name, stepCount, self.tracks, steps)
        self._zip.writestr(f'Sequences/{name}.sml', sml.encode('ascii'))
        return name

    def sliceWaveform(self, wav):
        """
        """
        markers = ()
        if isinstance(wav, tuple):
            wav, *markers = wav

        N = wav.shape[0]

        if N % self.minLen != 0:
            length = ((N // self.minLen) + 1) * self.minLen
        else:
            length = N

        points = np.zeros(length, dtype=np.float32)
        points[:N] = wav.astype(np.float32)

        if markers:
            markerData = np.zeros(length, dtype=np.uint8)
            markerData[:N] = markers[0].astype(np.uint8)
            for i, marker in enumerate(markers[1:], start=1):
                markerData[:N] |= marker.astype(np.uint8) << i
        else:
            markerData = None

        return [
            self.waveformName(
                points[i:i + self.minLen],
                markerData[i:i +
                           self.minLen] if markerData is not None else None)
            for i in range(0, length - 1, self.minLen)
        ]


class EasyBuilder():

    def __init__(self):
        self.tracks = 0
        self._waveforms_buffer = defaultdict(lambda: [None for _ in range(8)])
        self._markers_buffer = defaultdict(
            lambda: [[None] * 4 for _ in range(8)])
        self._step_args = defaultdict(lambda: dict(wait='None',
                                                   goto='Next',
                                                   repeatCount=1,
                                                   jumpInput='None',
                                                   jumpTo='Next'))
        self._buit = False

    def setStepWaveform(self, waveform, step, track):
        """
        Args:
            waveform: np.ndarray
            step: int
            track: int
        """
        self.tracks = max(self.tracks, track + 1)
        self._waveforms_buffer[step][track] = waveform

    def setStepMarker(self, marker, index, step, track):
        """
        Args:
            marker: np.ndarray
            index: int
            step: int
            track: int
        """
        self.tracks = max(self.tracks, track + 1)
        self._markers_buffer[step][track][index - 1] = marker

    def setStepArgs(self, step, **kwds):
        """
        Args:
            step: int
            wait: 'None' | 'TrigA' | 'TrigB' | 'Internal'
            goto: 'Next' | int
            repeatCount: int, 0 for infinite
            jumpInput: 'None' | 'TrigA' | 'TrigB' | 'Internal'
            jumpTo: 'Next' | int
        """
        kwds = {
            k: v
            for k, v in kwds.items()
            if k in ('wait', 'goto', 'repeatCount', 'jumpInput', 'jumpTo')
        }
        self._step_args[step].update(kwds)

    def makeSequence(self, name='Sequence', path=None):
        try:
            step = max(self._waveforms_buffer.keys())
        except:
            step = 0

        self.builder = SequenceBuilder(name, self.tracks)

        for i in range(step):
            waveforms = []
            if i not in self._waveforms_buffer:
                raise ValueError(f'Step {i} not defined')
            for j in range(self.builder.tracks):
                waveform = self._waveforms_buffer[i][j]
                markers = [
                    mk for mk in self._markers_buffer[i][j] if mk is not None
                ]
                if len(markers) == 0:
                    waveforms.append(waveform)
                else:
                    waveforms.append((waveform, ) + tuple(markers))
            kw = self._step_args[i]
            self.builder.addStep(waveforms, **kw)

        self.builder.makeSequence(path)
        self._buit = True

    def seqx(self):
        if not self._buit:
            raise ValueError('Sequence not built yet')
        return self.builder.seqx()
