import {useEffect,useRef,useState, type FormEvent} from 'react'
import {ArrowUpLeft,ArrowUp,BookOpen,BookmarkCheck,ChevronLeft,Compass,FileText,GraduationCap,LayoutGrid,LoaderCircle,MessageCircle,Plus,ShieldCheck,Sparkles,TriangleAlert} from 'lucide-react'
import {api,type Answer,type Doc,type Health,type Inspection,type Source} from './api'
import {PlannerView} from './Planner'
import {SourcesView,SourceDialog,n} from './Sources'

type Tab='chat'|'planner'|'sources'
type Message={role:'user'|'assistant';text:string;result?:Answer}
const statusNames:Record<string,string>={answered:'إجابة موثّقة',partially_answered:'إجابة جزئية',needs_clarification:'نحتاج توضيحاً',insufficient_evidence:'المعلومات غير كافية',out_of_scope:'خارج نطاق الإرشاد',conflicting_sources:'تعارض بين المصادر'}
const examples=[{icon:BookmarkCheck,title:'السحب والإضافة',question:'شو الفرق بين أسحب المادة وأحذفها؟'},{icon:GraduationCap,title:'المساقات والمتطلبات',question:'شو المتطلب السابق لمساق 10641373؟'},{icon:ShieldCheck,title:'الحضور والغياب',question:'إذا غبت أكثر من المسموح، شو بصير؟'}]

export default function App({completed,onCompletedChange}:{completed:string[];onCompletedChange:(courses:string[])=>void}){
 const [tab,setTab]=useState<Tab>('planner'),[health,setHealth]=useState<Health|null>(null),[docs,setDocs]=useState<Doc[]>([]),[inspection,setInspection]=useState<Inspection|null>(null),[startupError,setStartupError]=useState('')
 const [messages,setMessages]=useState<Message[]>([]),[question,setQuestion]=useState(''),[session,setSession]=useState<string|undefined>(),[style,setStyle]=useState('formal'),[busy,setBusy]=useState(false),[chatError,setChatError]=useState(''),[source,setSource]=useState<Source|null>(null)
 const end=useRef<HTMLDivElement>(null),input=useRef<HTMLTextAreaElement>(null)
 async function refresh(){
  setStartupError('')
  try{const h=await api<Health>('/health');setHealth(h);if(h.indexed){const [d,i]=await Promise.all([api<Doc[]>('/documents'),api<Inspection>('/inspection')]);setDocs(d);setInspection(i)}}catch(e){setStartupError(e instanceof Error?e.message:'تعذّر الاتصال بالخادم.')}
 }
 useEffect(()=>{void refresh()},[])
 useEffect(()=>{if(messages.length)end.current?.scrollIntoView({behavior:'smooth'})},[messages,busy])
 async function ask(event?:FormEvent,example?:string){
  event?.preventDefault();const q=(example??question).trim();if(!q||busy)return
  setQuestion('');setChatError('');setMessages(old=>[...old,{role:'user',text:q}]);setBusy(true)
  try{const result=await api<Answer>('/chat',{question:q,conversation_id:session,style});setSession(result.conversation_id);setMessages(old=>[...old,{role:'assistant',text:result.answer,result}])}
  catch(e){setChatError(e instanceof Error?e.message:'تعذّر إرسال السؤال.');setQuestion(q)}finally{setBusy(false)}
 }
 function newChat(){if(busy)return;setMessages([]);setSession(undefined);setChatError('');setQuestion('');setTab('chat');input.current?.focus()}
 return <div className="app-shell" dir="rtl">
  <a className="skip-link" href="#main-content">انتقل إلى المحتوى</a>
  <aside className="sidebar">
   <a href="#" className="brand" onClick={e=>{e.preventDefault();setTab('chat')}} aria-label="دليل، الصفحة الرئيسية"><span className="brand-mark"><BookOpen size={25}/></span><span>دليل<span className="brand-caption">رفيق مسيرتك الجامعية</span></span></a>
   <div className="workspace-label">مساحتك الأكاديمية</div>
   <nav aria-label="التنقل الرئيسي">{([{key:'chat',label:'اسأل دليل',icon:MessageCircle},{key:'planner',label:'محاكي الخطة',icon:LayoutGrid},{key:'sources',label:'مكتبة المصادر',icon:BookOpen}] as const).map(item=><button key={item.key} className={`nav-item ${tab===item.key?'active':''}`} onClick={()=>setTab(item.key)} aria-current={tab===item.key?'page':undefined}><item.icon size={20}/><span>{item.label}</span>{tab===item.key&&<span className="nav-dot"/>}</button>)}</nav>
   <div className="sidebar-divider"/><button className="new-chat" onClick={newChat} disabled={busy}><Plus size={18}/>محادثة جديدة</button>
   <div className="sidebar-note"><span className="note-icon"><Sparkles size={21}/></span><h3>احكيها بطريقتك.</h3><p>فصحى أو شامية، اسأل سؤالك ودليل يبحث في وثائق الجامعة.</p><span className="tiny-tag">مصدر واضح لكل معلومة</span></div>
   <div className="sidebar-bottom"><span className="university-monogram">ن</span><div><strong>جامعة النجاح الوطنية</strong><span>هندسة الحاسوب · نموذج تجريبي</span></div></div>
  </aside>
  <div className="main-shell">
   <header className="topbar"><div className="breadcrumb">مساحتك الأكاديمية <ChevronLeft size={14}/><strong>{tab==='chat'?'اسأل دليل':tab==='planner'?'محاكي الخطة':'مكتبة المصادر'}</strong></div><div className="topbar-status"><span className={`status-dot ${health?.indexed?'ready':''}`}/>{health?.indexed?'المعرفة جاهزة':'بانتظار الفهرسة'}<span className="header-divider"/><span className="demo-pill">نسخة الهاكاثون</span></div></header>
   <main id="main-content">
   {startupError&&<div className="alert error" role="alert"><TriangleAlert size={18}/><span>{startupError}</span><button onClick={()=>void refresh()}>إعادة المحاولة</button></div>}
   {health&&!health.indexed&&<div className="alert" role="status"><TriangleAlert size={18}/>جهّز قاعدة المعرفة بتشغيل أمر الفهرسة الموضّح في README.</div>}
   {tab==='chat'&&<div className={`chat-page ${messages.length?'has-messages':''}`}>
    {!messages.length?<>
     <div className="welcome-label"><span/> مساحة لأسئلتك، وإجابات بمصادرها</div>
     <div className="hero-icon"><Compass size={34} strokeWidth={1.4}/><span className="hero-star">✦</span></div>
     <h1>خطوتك القادمة، <em>أوضح.</em></h1>
     <p className="hero-description">من لوائح الجامعة إلى متطلبات مساقك.<br/>اسأل دليل، وخذ إجابة تستند إلى المصدر.</p>
     <div className="trust-row"><span><ShieldCheck size={16}/>إجابات من وثائق الجامعة</span><span className="trust-dot">·</span><span>بالعربية، وبلهجتك</span></div>
     <div className="suggestion-heading">من وين نبلّش؟ <span>جرّب واحداً من هذه الأسئلة</span></div>
     <div className="suggestions">{examples.map(item=><button key={item.title} onClick={()=>void ask(undefined,item.question)} disabled={busy}><span className="suggestion-icon"><item.icon size={20}/></span><strong>{item.title}</strong><p>{item.question}</p><ArrowUpLeft size={17} className="suggestion-arrow"/></button>)}</div>
    </>:<div className="conversation"><div className="conversation-heading"><span className="eyebrow">مساحة الحوار</span><h1>خلّينا نوضّح الصورة.</h1><button className="text-button" onClick={newChat} disabled={busy}><Plus size={15}/>محادثة جديدة</button></div>{messages.map((message,index)=><article key={index} className={`message ${message.role}`}><span className="message-avatar">{message.role==='user'?'أنت':<BookOpen size={19}/>}</span><div className="message-content"><div className="message-byline">{message.role==='user'?'سؤالك':'دليل'}{message.result&&<span className={`answer-status ${message.result.status}`}>{statusNames[message.result.status]}</span>}</div><div className="message-text">{message.text}</div>{message.result&&message.result.sources.length>0&&<div className="citations">{message.result.sources.map((s,i)=><button key={s.source_id} onClick={()=>setSource(s)}><span>{i+1}</span><FileText size={13}/>{s.page_start?`صفحة ${n(s.page_start)}`:s.document_name}<ChevronLeft size={12}/></button>)}</div>}{message.result?.limitations?.length?<div className="answer-limitations">{message.result.limitations.map((l,i)=><p key={i}>{l}</p>)}</div>:null}</div></article>)}{busy&&<div className="thinking" role="status"><LoaderCircle size={19} className="spin"/>يبحث دليل في المصادر ويتحقق من الإجابة…</div>}<div ref={end}/></div>}
    <div className="composer-area">{chatError&&<div className="alert error" role="alert"><TriangleAlert size={17}/>{chatError}</div>}{health&&!health.generation_configured&&<div className="setup-note"><span className="status-dot"/>الدردشة بانتظار إعداد مفتاح Gemini محلياً. يمكنك استكشاف المصادر ومحاكي الخطة الآن.</div>}
     <form className="composer" onSubmit={e=>void ask(e)}><label htmlFor="question" className="sr-only">سؤالك الأكاديمي</label><textarea id="question" ref={input} placeholder="شو حاب تعرف عن دراستك؟" value={question} onChange={e=>setQuestion(e.target.value)} maxLength={2000} rows={2} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();void ask()}}}/><div className="composer-bottom"><div className="composer-options"><BookOpen size={15}/><span>وثائق الجامعة</span><span className="option-divider"/><label htmlFor="style" className="sr-only">أسلوب الإجابة</label><select id="style" value={style} onChange={e=>setStyle(e.target.value)}><option value="formal">فصحى مبسّطة</option><option value="levantine">شامي فلسطيني</option></select></div><button type="submit" className="send-button" disabled={!question.trim()||busy} aria-label="إرسال السؤال">{busy?<LoaderCircle size={19} className="spin"/>:<ArrowUp size={20}/>}</button></div></form>
     <p className="composer-footnote"><ShieldCheck size={13}/>إذا لم تكفِ المصادر، سيخبرك دليل. الإرشاد هنا لا يغني عن قرار الجامعة.</p>
    </div>
    {!messages.length&&<div className="knowledge-strip"><span className="knowledge-icon"><FileText size={22}/></span><div><strong>المعرفة تبدأ من مصدرها.</strong><p>{health?.indexed?`${n(docs.length)} مصادر مفهرسة · ${n(health.chunks)} مقطعاً قابلاً للبحث`:'دليل الطالب والخطة الدراسية والأسئلة الشائعة'}</p></div><button onClick={()=>setTab('sources')}>استكشف المكتبة <ChevronLeft size={15}/></button></div>}
   </div>}
   {tab==='planner'&&<PlannerView onSource={setSource} initialCompleted={completed} onCompletedChange={onCompletedChange}/>}
   {tab==='sources'&&<SourcesView docs={docs} inspection={inspection} health={health}/>}
   </main>
   <footer className="site-footer"><span>دليل — معرفة موثّقة، وقرار أوضح.</span><span>صُنع للطالب العربي <span className="footer-star">✦</span></span></footer>
  </div>
  {source&&<SourceDialog source={source} onClose={()=>setSource(null)}/>}
 </div>
}
