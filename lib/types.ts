export type FormField = { id: string; label: string; type: string; section: string; required: boolean; instructions: string; options: {value:string;label:string}[]; constraints: Record<string,string>; required_when: string|null; evidence: {selector:string;label:string;instructions:string} };
export type SupportedForm = {id:string;title:string;instructions:string;source_hash:string;fields:FormField[];requirements:{id:string;text:string;selector:string}[];ambiguities:string[];demo_values?:Record<string,string>};
export type Draft = {id:string;form_id:string;source_hash:string;answers:Record<string,string|boolean>;checklist:string[];step:number;revision:number;status:string;receipt:string|null;updated_at:string;events?:{event:string;created_at:string;detail:string}[]};
export type Explanations = {fields:{field_id:string;plain_label:string;explanation:string}[];model:string;seconds:number;cached:boolean;verification:string};
export type Health = {status:string;portal_url:string;model:{ready:boolean;model:string;busy:boolean;local:boolean;detail:string;provider?:string;verified?:boolean};deployment?:{mode:'local'|'hosted';synthetic_only:boolean;draft_ttl_seconds:number|null;storage:string;inference:string}};
export async function api<T>(path:string, options?:RequestInit):Promise<T> {
  const response = await fetch(`/api${path}`, {credentials:'same-origin', cache:'no-store', signal:AbortSignal.timeout(path.endsWith('/explain')?255000:75000), ...options, headers:{'Content-Type':'application/json',...options?.headers}});
  const text = await response.text();
  let body;
  try { body = JSON.parse(text); } catch {
    throw new Error(response.ok ? 'The service returned an unreadable response. Please retry.' : 'The service did not respond in time. Your draft is still saved. Please retry.');
  }
  if(!response.ok) {
    const detail = body.detail;
    throw new Error(typeof detail === 'string' ? detail : detail?.message ? `${detail.message} ${Object.values(detail.fields || {}).join(' ')}` : 'The request could not be completed.');
  }
  return body;
}
