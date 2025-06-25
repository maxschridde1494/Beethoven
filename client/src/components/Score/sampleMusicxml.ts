// sample-musicxml.js
export const sampleXML = `<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE score-partwise PUBLIC
  "-//Recordare//DTD MusicXML 3.1 Partwise//EN"
  "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="3.1">
  <part-list>
    <score-part id="P1">
      <part-name>Piano</part-name>
      <score-instrument id="P1-I1"><instrument-name>Acoustic Grand</instrument-name></score-instrument>
      <midi-instrument id="P1-I1">
        <midi-channel>1</midi-channel>
        <midi-program>1</midi-program>
      </midi-instrument>
    </score-part>
  </part-list>

  <!--––– Part begins –––-->
  <part id="P1">
    <!-- Measure 1: single staff, middle-C whole note -->
    <measure number="1">
      <attributes>
        <divisions>4</divisions>            <!-- quarter-note = 4 MIDI ticks -->
        <key><fifths>0</fifths></key>       <!-- C major -->
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>

      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>16</duration>             <!-- 4 beats × divisions=4 -->
        <type>whole</type>
      </note>

      <barline location="right"><bar-style>light-heavy</bar-style></barline>
    </measure>

    <!-- Measure 2: grand staff with both hands -->
    <measure number="2">
      <attributes>
        <staves>2</staves>
        <divisions>4</divisions>
        <clef number="1"><sign>G</sign><line>2</line></clef>
        <clef number="2"><sign>F</sign><line>4</line></clef>
        <time><beats>4</beats><beat-type>4</beat-type></time>
      </attributes>

      <!-- Right-hand quarter notes -->
      <note staff="1">
        <pitch><step>E</step><octave>4</octave></pitch>
        <duration>4</duration><type>quarter</type>
      </note>
      <note staff="1">
        <pitch><step>G</step><octave>4</octave></pitch>
        <duration>4</duration><type>quarter</type>
      </note>
      <note staff="1">
        <pitch><step>C</step><octave>5</octave></pitch>
        <duration>4</duration><type>quarter</type>
      </note>
      <note staff="1">
        <pitch><step>D</step><octave>5</octave></pitch>
        <duration>4</duration><type>quarter</type>
      </note>

      <!-- Left-hand half notes -->
      <note staff="2">
        <pitch><step>C</step><octave>3</octave></pitch>
        <duration>8</duration><type>half</type>
      </note>
      <note staff="2">
        <pitch><step>G</step><octave>2</octave></pitch>
        <duration>8</duration><type>half</type>
      </note>

      <barline location="right"><bar-style>light-heavy</bar-style></barline>
    </measure>
  </part>
</score-partwise>`;