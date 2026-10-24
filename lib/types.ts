export type FormField = { id: string; label: string; type: string; section: string; required: boolean; instructions: string; options: {value:string;label:string}[]; constraints: Record<string,string>; required_when: string|null; evidence: {selector:string;label:string;instructions:string} };
export type SupportedForm = {id:string;title:string;instructions:string;source_hash:string;fields:FormField[];requirements:{id:string;text:string;selector:string}[];ambiguities:string[]};
export type Draft = {id:string;form_id:string;source_hash:string;answers:Record<string,string|boolean>;checklist:string[];step:number;revision:number;status:string;receipt:string|null;updated_at:string;events?:{event:string;created_at:string;detail:string}[]};
export type Explanations = {fields:{field_id:string;plain_label:string;explanation:string}[];model:string;seconds:number;cached:boolean;verification:string};
export type Health = {status:string;portal_url:string;model:{ready:boolean;model:string;busy:boolean;local:boolean;detail:string}};
export async function api<T>(path:string, options?:RequestInit):Promise<T> {
  const response = await fetch(`/api${path}`, {...options, headers:{'Content-Type':'application/json',...options?.headers}});
  const body = await response.json();
  if(!response.ok) {
    const detail = body.detail;
    throw new Error(typeof detail === 'string' ? detail : detail?.message ? `${detail.message} ${Object.values(detail.fields || {}).join(' ')}` : 'The local request could not be completed.');
  }
  return body;
}
