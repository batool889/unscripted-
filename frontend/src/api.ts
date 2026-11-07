export type Source={source_id:string;document_id:string;document_name:string;source_url:string;page_start:number|null;page_end:number|null;printed_page:string|null;article_number:string|null;record_id:string|null;excerpt:string;verification_status:string;version:string}
export type Answer={answer:string;status:string;sources:Source[];conversation_id:string;clarification_question?:string;limitations:string[];usage:Record<string,unknown>}
export type Health={status:string;indexed:boolean;semantic:boolean;chunks:number;generation_configured:boolean;gemini_model:string;scope:string}
export type Doc={document_id:string;document_name:string;filename:string;version:string;source_url:string;chunks:number;page_count?:number;rows?:number;verification_status:string}
export type Course={course_code:string;course_name_ar:string;course_name_en:string;credit_hours:string;requirement_group:string;prerequisite_expression:string;prerequisite_review_status:string;eligibility_note:string;source_url:string;source_document_id:string;source_record_id:string;review_reason?:string}
export type Plan={completion_checks?:{course_code:string;course_name_ar:string;prerequisite_expression:string}[];completed_count:number;earned_credits:number;counted_credits:number;remaining_credits:number;plan_total:number;categories:{key:string;label:string;earned:number;counted:number;required:number;remaining:number}[];eligible:Course[];needs_review:Course[];blocked:Course[];proposed_credits:number;proposal_valid:boolean;warnings:string[];graduation_confirmed:boolean}
export type Inspection={documents:number;chunks:number;courses:number;degree_conflicts:{value:number;page:number;excerpt:string}[];warnings:{issue:string;page?:number;document?:string}[]}
export async function api<T>(path:string,body?:unknown):Promise<T>{
 const response=await fetch('/api'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(150000)})
 const data=await response.json()
 if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'تعذّر تنفيذ الطلب. تحقق من المدخلات وحاول مجدداً.')
 return data as T
}
export function searchText(text:string){return text.normalize('NFKC').replace(/[\u064b-\u065fـ]/g,'').replace(/[أإآ]/g,'ا').replace(/ى/g,'ي').toLowerCase()}
export const groups:Record<string,string>={university:'إجباري الجامعة',major_required:'إجباري التخصص',major_elective:'اختياري التخصص',free_elective_option:'اختياري حر'}
