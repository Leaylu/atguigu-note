'use strict';
const $ = id => document.getElementById(id);
const state = {query:null,offset:0,next:null,ticketOffset:0,workflow:null,approval:null,decision:null};
const PAGE=2, TICKETS=10;
const names={awaiting_approval:'等待人工审批',completed:'处理完成',rejected:'已拒绝',no_action:'无需处理',not_started:'尚未开始',failed:'执行失败'};
const titles={orders:['异常订单','从订单事实出发，定位发货延迟。'],workflow:['处理工作流','先排查，再审批，最后创建工单。'],tickets:['工单记录','让处理过程留下可追溯的记录。'],approval:['人工审批','核对报告，以审批人身份提交决定。']};
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function notice(text,error=false){$('notice').hidden=false;$('notice').textContent=text;$('notice').className=error?'error':'';}
async function action(button,task){const was=button.disabled;button.disabled=true;button.setAttribute('aria-busy','true');try{await task();}catch(e){notice(e.message,true);}finally{button.disabled=was;button.removeAttribute('aria-busy');}}
async function api(path,{method='GET',body,approval=false}={}){
 const token=$(approval?'approver-token':'agent-token').value.trim();if(!token)throw Error(approval?'请填写审批令牌。':'请先填写 Agent 令牌。');
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);
 try{
 const res=await fetch(path,{method,headers:{Authorization:'Bearer '+token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:controller.signal,cache:'no-store'});
 const data=await res.json().catch(()=>({detail:'响应不是有效 JSON'}));
 if(!res.ok){let detail=data.detail;if(Array.isArray(detail))detail=detail.map(x=>x.loc.join('.')+'：'+x.msg).join('\n');throw Error('HTTP '+res.status+' · '+(detail||'请求失败'));}
 return data;
 }catch(e){if(e.name==='AbortError')throw Error('请求超时。操作结果可能已保存，请查询状态后再试；启动重试请保留请求编号。');throw e;}finally{clearTimeout(timer);}
}
function params(){const paid=$('paid-on').value,time=$('as-of').value;if(!paid||!time)throw Error('请填写支付日期和判断基准时间。');return {paid_on:paid,as_of:(time.length===16?time+':00':time)+'+08:00'};}
function empty(tbody,cols,message){const tr=node('tr'),td=node('td',message,'empty');td.colSpan=cols;tr.append(td);$(tbody).replaceChildren(tr);}
function date(value){return value?new Date(value).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false}):'—';}
function badge(text,cls='neutral'){return node('span',text,'badge '+cls);}
function switchView(name){document.querySelectorAll('.view').forEach(x=>x.hidden=x.id!==name);document.querySelectorAll('.nav').forEach(x=>{x.classList.toggle('active',x.dataset.view===name);if(x.dataset.view===name)x.setAttribute('aria-current','page');else x.removeAttribute('aria-current');});$('page-title').textContent=titles[name][0];$('page-description').textContent=titles[name][1];$('notice').hidden=true;}
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>switchView(b.dataset.view)));
$('clear-token').onclick=()=>{$('agent-token').value='';$('agent-token').dispatchEvent(new Event('input'));notice('Agent 令牌已清空。');};
$('agent-token').addEventListener('input',()=>{$('order-total').textContent='—';$('order-count').textContent='等待查询';empty('order-rows',6,'身份已变化，请重新查询。');$('evidence').hidden=true;state.query=null;state.workflow=null;$('workflow-result').textContent='身份已变化，请重新查询工作流。';$('resume-workflow').disabled=true;empty('ticket-rows',4,'身份已变化，请刷新工单。');$('order-prev').disabled=$('order-next').disabled=true;$('ticket-prev').disabled=$('ticket-next').disabled=true;});
async function loadOrders(offset,query){
 const q=new URLSearchParams({...query,offset,limit:PAGE}),result=await api('/orders?'+q);
 state.query=query;state.offset=offset;state.next=result.next_offset;
 $('order-total').textContent=result.total;$('order-count').textContent='本页 '+result.items.length+' / 共 '+result.total+' 条';
 $('order-page').textContent='第 '+(Math.floor(offset/PAGE)+1)+' 页';$('order-prev').disabled=offset===0;$('order-next').disabled=result.next_offset===null;
 if(!result.items.length){empty('order-rows',6,'当前范围没有超时未发货订单。');return;}
 $('order-rows').replaceChildren(...result.items.map(item=>{
 const tr=node('tr');[item.id,item.sku,item.quantity,date(item.paid_at)].forEach((v,i)=>tr.append(node('td',v,i===0?'order-id':undefined)));
 const status=node('td');status.append(badge('已支付 · 未发货','amber'));tr.append(status);
 const td=node('td'),b=node('button','查看证据','secondary');b.onclick=()=>action(b,()=>loadEvidence(item.id));td.append(b);tr.append(td);return tr;}));
}
$('query-form').onsubmit=e=>{e.preventDefault();action($('query-button'),async()=>{const query=params();$('evidence').hidden=true;$('order-total').textContent='—';empty('order-rows',6,'正在查询…');$('order-prev').disabled=$('order-next').disabled=true;await loadOrders(0,query);notice('查询完成，已读取服务端业务数据。');});};
$('order-prev').onclick=()=>action($('order-prev'),()=>loadOrders(Math.max(0,state.offset-PAGE),state.query)).then(()=>{$('order-prev').disabled=state.offset===0;});
$('order-next').onclick=()=>action($('order-next'),()=>loadOrders(state.next,state.query)).then(()=>{$('order-next').disabled=state.next===null;});
async function loadEvidence(id){
 const r=await api('/orders/'+encodeURIComponent(id)+'/evidence');$('evidence-title').textContent=id+' · 订单证据';
 const facts=node('div',undefined,'facts');
 for(const [label,text] of [['库存',r.inventory?'当前可用 '+r.inventory.available+' 件 / 订单需要 '+r.order.quantity+' 件':'库存记录缺失'],['履约',r.fulfillment?r.fulfillment.note:'暂无履约记录'],['可能原因',r.analysis.possible_reason],['建议核查',r.analysis.suggestion]]){
 const item=node('div',undefined,'fact');item.append(node('b',label),node('p',text));facts.append(item);}
 $('evidence-body').replaceChildren(facts,node('p','库存为当前快照；可能原因仍需业务核实。','muted'));$('evidence').hidden=false;
}
$('close-evidence').onclick=()=>$('evidence').hidden=true;
function newRequest(){$('request-id').value='web-'+crypto.randomUUID();}
newRequest();$('new-request').onclick=newRequest;
function renderWorkflow(r,target){
 const box=$(target);box.replaceChildren();const head=node('div',undefined,'workflow-state');head.append(badge(names[r.status]||r.status,r.status==='completed'?'good':r.status==='failed'?'bad':'amber'),node('span','审批：'+({approve:'已批准',reject:'已拒绝'}[r.decision]||'尚未提交'),'muted'));box.append(head);
 const steps=node('div',undefined,'flow-steps');['排查报告','人工决定','恢复流程','工单结果'].forEach(t=>steps.append(node('span',t)));box.append(steps);
 for(const row of r.report||[]){const item=node('div',undefined,'report-item');item.append(node('strong',row.order.id+' · '+row.order.sku),node('p',row.analysis.possible_reason),node('p',row.analysis.suggestion));box.append(item);}
 if(!(r.report||[]).length)box.append(node('p','当前没有待处理订单。','muted'));
 for(const ticket of r.tickets||[])box.append(node('p',(ticket.id||ticket.order_id)+' · '+({created:'新建工单',existing:'复用已有工单',skipped_changed:'订单状态变化，已跳过'}[ticket.outcome]||ticket.status),'muted'));
}
function setWorkflow(r){state.workflow=r;$('workflow-id').value=r.workflow_id;renderWorkflow(r,'workflow-result');$('resume-workflow').disabled=!(r.status==='awaiting_approval'&&r.decision);}
$('start-workflow').onclick=()=>action($('start-workflow'),async()=>{const request_id=$('request-id').value.trim();if(!/^[a-zA-Z0-9_-]{1,64}$/.test(request_id))throw Error('请求编号限1—64个字母、数字、下划线或连字符。');const r=await api('/workflows',{method:'POST',body:{...params(),request_id}});setWorkflow(r);notice('排查流程已返回：'+(names[r.status]||r.status)+'。');});
$('workflow-refresh').onclick=()=>action($('workflow-refresh'),async()=>{const id=$('workflow-id').value.trim();if(!id)throw Error('请填写工作流编号。');setWorkflow(await api('/workflows/'+encodeURIComponent(id)));});
$('workflow-id').oninput=()=>{state.workflow=null;$('resume-workflow').disabled=true;};
$('resume-workflow').onclick=async()=>{const b=$('resume-workflow');await action(b,async()=>{const id=$('workflow-id').value.trim();const r=await api('/workflows/'+encodeURIComponent(id)+'/resume',{method:'POST'});setWorkflow(r);notice('流程状态：'+(names[r.status]||r.status)+'。处理完成表示工单流程完成，不代表已经发货。');});b.disabled=!(state.workflow?.status==='awaiting_approval'&&state.workflow.decision);};
async function loadTickets(offset=0){const r=await api('/tickets?'+new URLSearchParams({offset,limit:TICKETS}));state.ticketOffset=offset;
 $('ticket-prev').disabled=offset===0;$('ticket-next').disabled=r.items.length<TICKETS;$('ticket-page').textContent='第 '+(Math.floor(offset/TICKETS)+1)+' 页';
 if(!r.items.length){empty('ticket-rows',4,'本页没有工单。');return;}
 $('ticket-rows').replaceChildren(...r.items.map(t=>{const tr=node('tr');[t.id,t.order_id,t.status==='open'?'待处理':t.status,t.workflow_id].forEach(v=>tr.append(node('td',v)));return tr;}));}
$('tickets-refresh').onclick=()=>action($('tickets-refresh'),()=>loadTickets(0));
$('ticket-prev').onclick=async()=>{await action($('ticket-prev'),()=>loadTickets(Math.max(0,state.ticketOffset-TICKETS)));$('ticket-prev').disabled=state.ticketOffset===0;};
$('ticket-next').onclick=async()=>{const b=$('ticket-next');await action(b,()=>loadTickets(state.ticketOffset+TICKETS));b.disabled=$('ticket-rows').querySelectorAll('tr').length<TICKETS;};
function approvalState(r){state.approval=r;renderWorkflow(r,'approval-report');const can=r.status==='awaiting_approval'&&!r.decision;$('approve').disabled=$('reject').disabled=!can;}
$('approval-form').onsubmit=e=>{e.preventDefault();action(e.submitter,async()=>{const id=$('approval-id').value.trim();approvalState(await api('/workflows/'+encodeURIComponent(id),{approval:true}));});};
for(const id of ['approval-id','approver-token'])$(id).addEventListener('input',()=>{state.approval=null;$('approve').disabled=$('reject').disabled=true;$('approval-report').textContent='信息已变化，请重新读取待审批报告。';});
function askDecision(decision){if(!state.approval)return;state.decision=decision;$('decision-title').textContent=decision==='approve'?'确认批准创建工单':'确认拒绝处理';
 $('decision-description').textContent='工作流 '+state.approval.workflow_id+'，报告含 '+(state.approval.report||[]).length+' 个订单。审批决定提交后不可改写。';$('decision-confirm').value='';$('decision-dialog').showModal();}
$('approve').onclick=()=>askDecision('approve');$('reject').onclick=()=>askDecision('reject');$('decision-cancel').onclick=()=>$('decision-dialog').close();
$('decision-submit').onclick=()=>action($('decision-submit'),async()=>{const r=state.approval;if(!r||$('decision-confirm').value.trim()!==r.workflow_id)throw Error('请输入正确的完整工作流编号。');
 const updated=await api('/workflows/'+encodeURIComponent(r.workflow_id)+'/decision',{method:'POST',approval:true,body:{decision:state.decision}});approvalState(updated);$('decision-dialog').close();$('approver-token').value='';notice('审批决定已保存。请回到处理工作流，查询状态后继续执行。');});
fetch('/health',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(()=>{$('health').textContent='● 服务已连接';$('health').className='badge good';}).catch(()=>{$('health').textContent='服务未连接';$('health').className='badge bad';});
