"""Time hosted-aware narration to the genuine public Render capture."""
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'demo/assets/render'


def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True)


def main():
    capture=json.loads((ASSETS/'recording-evidence.json').read_text(encoding='utf-8'))
    assert capture['public_url']=='https://accesspath-demo.onrender.com' and capture['full_decode_passed']
    markers=capture['markers']
    lead=round(max(0,markers['opening']-.6)*25)/25 if markers['opening']>1.5 else 0
    video=ASSETS/'video/demo_silent.mp4'
    if lead:
        raw=max((ASSETS/'video/raw').glob('*.webm'),key=lambda p:p.stat().st_mtime)
        run(['ffmpeg','-v','error','-y','-ss',str(lead),'-i',str(raw),'-c:v','libx264','-preset','fast','-crf','21','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(video)])
        markers={k:round(max(0,v-lead),3) for k,v in markers.items()}
    probe=json.loads(run(['ffprobe','-v','error','-show_entries','format=duration,size','-of','json',str(video)]).stdout)
    duration=float(probe['format']['duration'])
    texts={
        'opening':'AccessPath is now live on Render. Explore fictional forms using synthetic sample answers.',
        'original':'The scholarship form is fictional, but its language is deliberately difficult. Here is the original source, before guidance.',
        'evidence':'Hosted Qwen explains source instructions through Groq. Your answers are excluded. Compare each suggestion with the original.',
        'preparation':'Confirm the source checklist. No documents are uploaded.',
        'questions':'Use the supplied sample answers, one question at a time. Choices and required fields follow the source. This public demo accepts synthetic details only.',
        'statement':"The statement keeps the source limits. Sample text demonstrates completion without collecting a real applicant's story.",
        'confirmation':'Review before sending. The submit button stays disabled until you confirm. Editing an answer invalidates that confirmation.',
        'receipt':'A real browser submits only the private fictional portal. This receipt confirms the demo action, without contacting a real agency.',
        'privacy':'Synthetic drafts stay temporarily on Render, not on your device. Delete your draft and activity, or let it expire.',
    }
    scenes=[];names=list(texts)
    for i,name in enumerate(names):
        scene={'id':name,'start':round(markers[name]+.15,3),'end':round(markers[names[i+1]]-.2,3) if i+1<len(names) else round(duration-.3,3),'text':texts[name]}
        if name=='evidence':scene['tts_text']=texts[name].replace('Qwen','[Qwen](/kw\u02c8\u025bn/)')
        assert scene['end']>scene['start']
        scenes.append(scene)
    timeline={'voice':'am_liam','voice_display_name':'Liam','voice_selected_by':'user','sample_rate':24000,'video_duration':duration,'public_url':capture['public_url'],'theme':'midnight-blue-hosted','scenes':scenes}
    audio=ASSETS/'audio';audio.mkdir(parents=True,exist_ok=True)
    (audio/'narration_timeline.json').write_text(json.dumps(timeline,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    script='# AccessPath Render narration\n\nVoice: Liam, selected by the user. Timings follow the actual public recording.\n\n'
    for scene in scenes:script+=f"## {scene['start']:.2f}-{scene['end']:.2f}: {scene['id']}\n\n{scene['text']}\n\n"
    (audio/'narration_script.md').write_text(script.rstrip()+'\n',encoding='utf-8')
    capture.update(final_duration_seconds=duration,lead_trim_seconds=lead,trim_note='Only initial page-loading lead removed; no inference or submission waiting time removed.',narration_status='Timeline prepared for selected Liam voice.')
    (ASSETS/'recording-evidence.json').write_text(json.dumps(capture,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'duration':duration,'lead_trim':lead,'scenes':[{k:s[k] for k in ['id','start','end']} for s in scenes]}))


if __name__=='__main__':main()
