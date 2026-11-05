import{s as j,R as q,x,v as z,d as Q,k as o,P as X,y as Z,B as U,S as oe,e as O,C as ee,F as V,T as re,U as de,r as A,c as L,b as u,f as c,O as s,_ as ce,o as h,a as _,h as R,i as T,V as K,H as ue,j as D,t as F,Q as ve,l as pe}from"./index-B4HPkA4u.js";import{a as me,_ as fe,b as _e}from"./Spin-CqnYMMMq.js";import{_ as ge}from"./Alert-Ba28YsNr.js";import{a as be,_ as he}from"./DescriptionsItem-DTPMNTho.js";import{N as xe,_ as ye}from"./DataTable-Uo5-CKev.js";import{_ as Ce}from"./Empty-aJramja4.js";const ke=j("divider",`
 position: relative;
 display: flex;
 width: 100%;
 box-sizing: border-box;
 font-size: 16px;
 color: var(--n-text-color);
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
`,[q("vertical",`
 margin-top: 24px;
 margin-bottom: 24px;
 `,[q("no-title",`
 display: flex;
 align-items: center;
 `)]),x("title",`
 display: flex;
 align-items: center;
 margin-left: 12px;
 margin-right: 12px;
 white-space: nowrap;
 font-weight: var(--n-font-weight);
 `),z("title-position-left",[x("line",[z("left",{width:"28px"})])]),z("title-position-right",[x("line",[z("right",{width:"28px"})])]),z("dashed",[x("line",`
 background-color: #0000;
 height: 0px;
 width: 100%;
 border-style: dashed;
 border-width: 1px 0 0;
 `)]),z("vertical",`
 display: inline-block;
 height: 1em;
 margin: 0 8px;
 vertical-align: middle;
 width: 1px;
 `),x("line",`
 border: none;
 transition: background-color .3s var(--n-bezier), border-color .3s var(--n-bezier);
 height: 1px;
 width: 100%;
 margin: 0;
 `),q("dashed",[x("line",{backgroundColor:"var(--n-color)"})]),z("dashed",[x("line",{borderColor:"var(--n-color)"})]),z("vertical",{backgroundColor:"var(--n-color)"})]),we=Object.assign(Object.assign({},U.props),{titlePlacement:{type:String,default:"center"},dashed:Boolean,vertical:Boolean}),ze=Q({name:"Divider",props:we,setup(d){const{mergedClsPrefixRef:l,inlineThemeDisabled:p}=Z(d),g=U("Divider","-divider",ke,oe,d,l),y=O(()=>{const{common:{cubicBezierEaseInOut:t},self:{color:m,textColor:C,fontWeight:i}}=g.value;return{"--n-bezier":t,"--n-color":m,"--n-text-color":C,"--n-font-weight":i}}),r=p?ee("divider",void 0,y,d):void 0;return{mergedClsPrefix:l,cssVars:p?void 0:y,themeClass:r==null?void 0:r.themeClass,onRender:r==null?void 0:r.onRender}},render(){var d;const{$slots:l,titlePlacement:p,vertical:g,dashed:y,cssVars:r,mergedClsPrefix:t}=this;return(d=this.onRender)===null||d===void 0||d.call(this),o("div",{role:"separator",class:[`${t}-divider`,this.themeClass,{[`${t}-divider--vertical`]:g,[`${t}-divider--no-title`]:!l.default,[`${t}-divider--dashed`]:y,[`${t}-divider--title-position-${p}`]:l.default&&p}],style:r},g?null:o("div",{class:`${t}-divider__line ${t}-divider__line--left`}),!g&&l.default?o(X,null,o("div",{class:`${t}-divider__title`},this.$slots),o("div",{class:`${t}-divider__line ${t}-divider__line--right`})):null)}}),Se=j("statistic",[x("label",`
 font-weight: var(--n-label-font-weight);
 transition: .3s color var(--n-bezier);
 font-size: var(--n-label-font-size);
 color: var(--n-label-text-color);
 `),j("statistic-value",`
 margin-top: 4px;
 font-weight: var(--n-value-font-weight);
 `,[x("prefix",`
 margin: 0 4px 0 0;
 font-size: var(--n-value-font-size);
 transition: .3s color var(--n-bezier);
 color: var(--n-value-prefix-text-color);
 `,[j("icon",{verticalAlign:"-0.125em"})]),x("content",`
 font-size: var(--n-value-font-size);
 transition: .3s color var(--n-bezier);
 color: var(--n-value-text-color);
 `),x("suffix",`
 margin: 0 0 0 4px;
 font-size: var(--n-value-font-size);
 transition: .3s color var(--n-bezier);
 color: var(--n-value-suffix-text-color);
 `,[j("icon",{verticalAlign:"-0.125em"})])])]),$e=Object.assign(Object.assign({},U.props),{tabularNums:Boolean,label:String,value:[String,Number]}),Re=Q({name:"Statistic",props:$e,slots:Object,setup(d){const{mergedClsPrefixRef:l,inlineThemeDisabled:p,mergedRtlRef:g}=Z(d),y=U("Statistic","-statistic",Se,re,d,l),r=de("Statistic",g,l),t=O(()=>{const{self:{labelFontWeight:C,valueFontSize:i,valueFontWeight:H,valuePrefixTextColor:I,labelTextColor:M,valueSuffixTextColor:S,valueTextColor:B,labelFontSize:W},common:{cubicBezierEaseInOut:G}}=y.value;return{"--n-bezier":G,"--n-label-font-size":W,"--n-label-font-weight":C,"--n-label-text-color":M,"--n-value-font-weight":H,"--n-value-font-size":i,"--n-value-prefix-text-color":I,"--n-value-suffix-text-color":S,"--n-value-text-color":B}}),m=p?ee("statistic",void 0,t,d):void 0;return{rtlEnabled:r,mergedClsPrefix:l,cssVars:p?void 0:t,themeClass:m==null?void 0:m.themeClass,onRender:m==null?void 0:m.onRender}},render(){var d;const{mergedClsPrefix:l,$slots:{default:p,label:g,prefix:y,suffix:r}}=this;return(d=this.onRender)===null||d===void 0||d.call(this),o("div",{class:[`${l}-statistic`,this.themeClass,this.rtlEnabled&&`${l}-statistic--rtl`],style:this.cssVars},V(g,t=>o("div",{class:`${l}-statistic__label`},this.label||t)),o("div",{class:`${l}-statistic-value`,style:{fontVariantNumeric:this.tabularNums?"tabular-nums":""}},V(y,t=>t&&o("span",{class:`${l}-statistic-value__prefix`},t)),this.value!==void 0?o("span",{class:`${l}-statistic-value__content`},this.value):V(p,t=>t&&o("span",{class:`${l}-statistic-value__content`},t)),V(r,t=>t&&o("span",{class:`${l}-statistic-value__suffix`},t))))}}),Te={class:"mx-auto px-4 py-6 max-w-7xl w-full"},Be={class:"gap-4 grid grid-cols-1 items-end md:grid-cols-[240px_180px_auto]"},Ee={class:"space-y-1"},Ae={class:"space-y-1"},Oe={key:0,class:"space-y-6"},Me={class:"gap-4 grid grid-cols-1 sm:grid-cols-3"},Pe={key:1},De={class:"flex gap-2 items-center"},He=Q({__name:"licha",setup(d){const l=["券商债项","银行债项","信用债项","券商主体","银行主体","信用债主体","城投债项","城投主体","ABS专项"],p=[],g=new Date(2022,0,1),y=new Date(2025,6,1);for(let n=g;n<=y;n.setMonth(n.getMonth()+1))p.push(`${n.getFullYear()}-${String(n.getMonth()+1).padStart(2,"0")}`);const r=A(l[6]),t=A("2023-10"),m=A(!1),C=A(""),i=A(null),H=[{title:"评级",key:"评级",width:100},{title:"数量",key:"数量",render(n){return o("div",{class:"flex items-center gap-2"},[o("span",n.数量),o("div",{class:"flex-1 bg-gray-100 rounded-full h-2 dark:bg-dark-700 overflow-hidden"},[o("div",{class:"bg-blue-500 rounded-full h-2 transition-all",style:{width:`${Math.min(100,n.数量/I.value*100)}%`}})])])}}],I=O(()=>{var e,a;const n=(a=(e=i.value)==null?void 0:e.metrics)==null?void 0:a.各评级数量统计;return n?Math.max(1,...Object.values(n)):1}),M=O(()=>{var e,a;const n=((a=(e=i.value)==null?void 0:e.metrics)==null?void 0:a.各评级数量统计)||{};return Object.entries(n).map(([b,v])=>({评级:b,数量:v}))}),S=A(""),B=O(()=>{var a;const n=((a=i.value)==null?void 0:a.bond_list)||[],e=S.value.trim().toLowerCase();return e?n.filter(b=>String(b.代码??"").toLowerCase().includes(e)):n});function W(){const n=B.value;if(!n.length)return;const e=["数据类型","预测月份","代码","预测利差","评级结果"],a=e.join(","),b=n.map(P=>e.map(E=>P[E]!==void 0&&P[E]!==null?`"${String(P[E]).replace(/"/g,'""')}"`:"").join(",")),v=[a,...b].join(`
`),w="\uFEFF",k=new Blob([w+v],{type:"text/csv;charset=utf-8"}),N=URL.createObjectURL(k),$=document.createElement("a");$.href=N,$.download=`利差预测_${r.value}_${t.value}.csv`,$.click(),URL.revokeObjectURL(N)}const G=O(()=>{var b;const n=((b=i.value)==null?void 0:b.bond_list)||[];if(!n.length)return[];const e=Object.keys(n[0]);return[{key:"数据类型",title:"数据类型",width:110},{key:"预测月份",title:"预测月份",width:110},{key:"代码",title:"代码",width:140},{key:"预测利差",title:"预测利差",width:110},{key:"评级结果",title:"评级结果",width:100}].filter(v=>e.includes(v.key)).map(v=>({key:v.key,title:v.title,width:v.width,render(w){const k=w[v.key];return v.key==="评级结果"?o("n-tag",{type:te(String(k)),size:"small"},{default:()=>k}):v.key==="预测利差"&&typeof k=="number"?o("span",k.toFixed(4)):o("span",k??"-")}}))});function te(n){return{AAA级:"success","AA+级":"success",AA级:"info","A+级":"info",A级:"info",BBB级:"warning",BB级:"warning",B级:"error",CCC级:"error",CC级:"error",C级:"error"}[n]||"default"}const ne={pageSize:10,showSizePicker:!0,pageSizes:[10,20,50,100]};async function se(){var n,e;m.value=!0,C.value="",i.value=null,S.value="";try{const a=await pe.post("/ketiyi/licha",{SELECTED_DATASET:r.value,TARGET_MONTH:t.value},{headers:{"Content-Type":"application/json"}});a.data.status==="success"?i.value=a.data.data:C.value=a.data.message||"预测失败，请稍后重试"}catch(a){console.error("Licha prediction error:",a),C.value=((e=(n=a.response)==null?void 0:n.data)==null?void 0:e.message)||a.message||"预测失败，请稍后重试"}finally{m.value=!1}}return(n,e)=>{const a=fe,b=ue,v=ge,w=ce,k=he,N=be,$=Re,P=ze,E=xe,le=ye,ae=_e,Y=Ce,ie=me;return h(),L("div",Te,[u(w,{title:"利差预测",bordered:!1,class:"mb-6"},{default:c(()=>[e[7]||(e[7]=_("p",{class:"text-gray-700 mb-4 dark:text-gray-300"}," 选择数据集分类与预测月份，基于历史数据训练 GBDT 模型预测信用利差，并推演中文评级分布。 ",-1)),_("div",Be,[_("div",Ee,[e[3]||(e[3]=_("div",{class:"text-sm text-gray-500 dark:text-gray-400"}," 数据集分类 ",-1)),u(a,{value:s(r),"onUpdate:value":e[0]||(e[0]=f=>K(r)?r.value=f:null),options:l.map(f=>({label:f,value:f}))},null,8,["value","options"])]),_("div",Ae,[e[4]||(e[4]=_("div",{class:"text-sm text-gray-500 dark:text-gray-400"}," 预测月份 ",-1)),u(a,{value:s(t),"onUpdate:value":e[1]||(e[1]=f=>K(t)?t.value=f:null),options:p.map(f=>({label:f,value:f}))},null,8,["value","options"])]),u(b,{type:"primary",loading:s(m),onClick:se},{icon:c(()=>e[5]||(e[5]=[_("div",{class:"i-carbon-predictive-analysis"},null,-1)])),default:c(()=>[e[6]||(e[6]=D(" 开始预测 "))]),_:1},8,["loading"])]),s(C)?(h(),R(v,{key:0,type:"error",class:"mt-4",closable:""},{default:c(()=>[D(F(s(C)),1)]),_:1})):T("",!0)]),_:1}),u(ie,{show:s(m)},{default:c(()=>[s(i)?(h(),L("div",Oe,[u(w,{title:"预测信息",bordered:!1},{default:c(()=>[u(N,{column:3,bordered:"",size:"small"},{default:c(()=>[(h(!0),L(X,null,ve(s(i).meta_info,(f,J)=>(h(),R(k,{key:J,label:J},{default:c(()=>[D(F(f),1)]),_:2},1032,["label"]))),128))]),_:1})]),_:1}),u(w,{title:"预测效果",bordered:!1},{default:c(()=>[_("div",Me,[s(i).metrics.MAE!==void 0?(h(),R($,{key:0,label:"MAE 平均绝对误差",value:s(i).metrics.MAE},null,8,["value"])):T("",!0),s(i).metrics.RMSE!==void 0?(h(),R($,{key:1,label:"RMSE 均方根误差",value:s(i).metrics.RMSE},null,8,["value"])):T("",!0),s(i).metrics["R²"]!==void 0?(h(),R($,{key:2,label:"R² 决定系数",value:s(i).metrics["R²"]},null,8,["value"])):T("",!0)]),s(M).length?(h(),R(P,{key:0})):T("",!0),s(M).length?(h(),L("div",Pe,[e[8]||(e[8]=_("div",{class:"text-sm text-gray-500 mb-3 dark:text-gray-400"}," 各评级数量统计 ",-1)),u(E,{columns:H,data:s(M),bordered:!1,size:"small","max-height":300},null,8,["data"])])):T("",!0)]),_:1}),u(w,{title:"预测结果",bordered:!1},{"header-extra":c(()=>[_("div",De,[u(le,{value:s(S),"onUpdate:value":e[2]||(e[2]=f=>K(S)?S.value=f:null),clearable:"",placeholder:"搜索代码...",size:"small",class:"w-45"},{prefix:c(()=>e[9]||(e[9]=[_("div",{class:"i-carbon-search text-gray-500"},null,-1)])),_:1},8,["value"]),u(b,{size:"small",type:"primary",secondary:"",disabled:!s(B).length,onClick:W},{icon:c(()=>e[10]||(e[10]=[_("div",{class:"i-carbon-download"},null,-1)])),default:c(()=>[e[11]||(e[11]=D(" CSV "))]),_:1},8,["disabled"]),u(ae,{size:"small",type:"info"},{default:c(()=>[D(" 共 "+F(s(B).length)+" / "+F(s(i).bond_list.length)+" 只 ",1)]),_:1})])]),default:c(()=>[u(E,{columns:s(G),data:s(B),bordered:!1,"single-line":!1,pagination:ne,size:"small"},{empty:c(()=>[u(Y,{description:"暂无预测数据"})]),_:1},8,["columns","data"])]),_:1})])):s(C)?T("",!0):(h(),R(Y,{key:1,description:"选择参数后点击「开始预测」",class:"py-12"}))]),_:1},8,["show"])])}}});export{He as default};
