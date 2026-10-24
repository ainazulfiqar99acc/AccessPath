"""Align the selected narration to the actual refreshed recording's scene markers."""
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
VIDEO=ROOT/'demo/assets/video'
AUDIO=ROOT/'demo/assets/audio'


def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True)


def main():
    capture=json.loads((VIDEO/'scene-timing.json').read_text(encoding='utf-8'))
    markers=capture['markers']
    lead=round(max(0,markers['opening']-.6)*25)/25 if markers['opening']>1.5 else 0
    if lead:
        raw=Path(capture.get('raw_file') or max((VIDEO/'raw').glob('*.webm'),key=lambda p:p.stat().st_mtime))
        run(['ffmpeg','-v','error','-y','-ss',str(lead),'-i',str(raw),'-c:v','libx264',
             '-preset','fast','-crf','21','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(VIDEO/'demo_silent.mp4')])
        capture['raw_file']=str(raw)
        capture['lead_trim_seconds']=lead
        capture['markers']={name:round(max(0,value-lead),3) for name,value in markers.items()}
        markers=capture['markers']
    probe=json.loads(run(['ffprobe','-v','error','-show_entries','format=duration,size',
                          '-show_entries','stream=codec_name,width,height,pix_fmt','-of','json',str(VIDEO/'demo_silent.mp4')]).stdout)
    duration=float(probe['format']['duration'])
    capture['duration']=duration
    (VIDEO/'scene-timing.json').write_text(json.dumps(capture,indent=2),encoding='utf-8')
    timeline=json.loads((AUDIO/'narration_timeline.json').read_text(encoding='utf-8'))
    timeline['video_duration']=duration
    timeline['theme']='midnight-blue'
    for i,scene in enumerate(timeline['scenes']):
        scene['start']=round(markers[scene['id']]+(.15 if i==0 else .2),3)
        scene['end']=round(markers[timeline['scenes'][i+1]['id']]-.2,3) if i+1<len(timeline['scenes']) else round(duration-.5,3)
        assert scene['end']>scene['start']
    (AUDIO/'narration_timeline.json').write_text(json.dumps(timeline,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    script='# AccessPath narration\n\nVoice: Liam (American English, selected by the user). Timing follows the actual midnight-blue recording.\n\n'
    for s in timeline['scenes']:script+=f"## {s['start']:.2f}-{s['end']:.2f} seconds: {s['id']}\n\n{s['text']}\n\n"
    (AUDIO/'narration_script.md').write_text(script.rstrip()+'\n',encoding='utf-8')
    run(['ffmpeg','-v','error','-i',str(VIDEO/'demo_silent.mp4'),'-f','null','-'])
    (ROOT/'docs/video-evidence.json').write_text(json.dumps({'file':'demo/assets/video/demo_silent.mp4',
       'theme':'midnight-blue','decode_verified':True,**probe},indent=2),encoding='utf-8')
    print(json.dumps({'duration':duration,'lead_trim_seconds':lead,'scene_count':len(timeline['scenes'])}))


if __name__=='__main__':main()
