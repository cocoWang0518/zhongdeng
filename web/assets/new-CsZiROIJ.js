import{d as q,k as f,s as E,v as $,q as Y,x as l,R as ie,y as de,r as k,e as D,U as ve,B as ae,V as Be,X as he,C as me,D as ze,L as Ee,K,Y as Pe,Z as ge,$ as Ve,A as ce,a0 as Fe,a1 as ue,a2 as De,a3 as Ue,a4 as Ie,a5 as Te,m as je,N as Le,a6 as He,p as Me,a7 as Oe,a8 as We,a9 as pe,aa as re,F as O,ab as Ke,ac as qe,ad as Ye,ae as W,af as se,ag as U,w as Xe,c as J,o as M,b as u,h as ee,i as te,f as w,j as F,H as be,a as P,ah as Ze,t as V,P as Qe,Q as Ge,l as _e,ai as Je,_ as et,aj as tt,g as at}from"./index-ahexOs-Q.js";import{_ as lt,a as nt}from"./Image-uHAPC6LV.js";import{_ as ot,a as rt}from"./PredictForm.vue_vue_type_script_setup_true_lang-rqRnML_d.js";import{f as st,_ as we}from"./Alert-aEjxLQPu.js";import{h as fe,a as it,N as dt,b as ct}from"./Spin-qrraIwAO.js";import{_ as ut}from"./Statistic-DjhFthJv.js";import"./Empty-Gxdk5zcf.js";const pt=q({name:"ChevronLeft",render(){return f("svg",{viewBox:"0 0 16 16",fill:"none",xmlns:"http://www.w3.org/2000/svg"},f("path",{d:"M10.3536 3.14645C10.5488 3.34171 10.5488 3.65829 10.3536 3.85355L6.20711 8L10.3536 12.1464C10.5488 12.3417 10.5488 12.6583 10.3536 12.8536C10.1583 13.0488 9.84171 13.0488 9.64645 12.8536L5.14645 8.35355C4.95118 8.15829 4.95118 7.84171 5.14645 7.64645L9.64645 3.14645C9.84171 2.95118 10.1583 2.95118 10.3536 3.14645Z",fill:"currentColor"}))}}),ft=E("collapse","width: 100%;",[E("collapse-item",`
 font-size: var(--n-font-size);
 color: var(--n-text-color);
 transition:
 color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 margin: var(--n-item-margin);
 `,[$("disabled",[l("header","cursor: not-allowed;",[l("header-main",`
 color: var(--n-title-text-color-disabled);
 `),E("collapse-item-arrow",`
 color: var(--n-arrow-color-disabled);
 `)])]),E("collapse-item","margin-left: 32px;"),Y("&:first-child","margin-top: 0;"),Y("&:first-child >",[l("header","padding-top: 0;")]),$("left-arrow-placement",[l("header",[E("collapse-item-arrow","margin-right: 4px;")])]),$("right-arrow-placement",[l("header",[E("collapse-item-arrow","margin-left: 4px;")])]),l("content-wrapper",[l("content-inner","padding-top: 16px;"),st({duration:"0.15s"})]),$("active",[l("header",[$("active",[E("collapse-item-arrow","transform: rotate(90deg);")])])]),Y("&:not(:first-child)","border-top: 1px solid var(--n-divider-color);"),ie("disabled",[$("trigger-area-main",[l("header",[l("header-main","cursor: pointer;"),E("collapse-item-arrow","cursor: default;")])]),$("trigger-area-arrow",[l("header",[E("collapse-item-arrow","cursor: pointer;")])]),$("trigger-area-extra",[l("header",[l("header-extra","cursor: pointer;")])])]),l("header",`
 font-size: var(--n-title-font-size);
 display: flex;
 flex-wrap: nowrap;
 align-items: center;
 transition: color .3s var(--n-bezier);
 position: relative;
 padding: var(--n-title-padding);
 color: var(--n-title-text-color);
 `,[l("header-main",`
 display: flex;
 flex-wrap: nowrap;
 align-items: center;
 font-weight: var(--n-title-font-weight);
 transition: color .3s var(--n-bezier);
 flex: 1;
 color: var(--n-title-text-color);
 `),l("header-extra",`
 display: flex;
 align-items: center;
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 `),E("collapse-item-arrow",`
 display: flex;
 transition:
 transform .15s var(--n-bezier),
 color .3s var(--n-bezier);
 font-size: 18px;
 color: var(--n-arrow-color);
 `)])])]),vt=Object.assign(Object.assign({},ae.props),{defaultExpandedNames:{type:[Array,String],default:null},expandedNames:[Array,String],arrowPlacement:{type:String,default:"left"},accordion:{type:Boolean,default:!1},displayDirective:{type:String,default:"if"},triggerAreas:{type:Array,default:()=>["main","extra","arrow"]},onItemHeaderClick:[Function,Array],"onUpdate:expandedNames":[Function,Array],onUpdateExpandedNames:[Function,Array],onExpandedNamesChange:{type:[Function,Array],validator:()=>!0,default:void 0}}),xe=ze("n-collapse"),ht=q({name:"Collapse",props:vt,slots:Object,setup(e,{slots:v}){const{mergedClsPrefixRef:h,inlineThemeDisabled:o,mergedRtlRef:d}=de(e),n=k(e.defaultExpandedNames),_=D(()=>e.expandedNames),y=ve(_,n),x=ae("Collapse","-collapse",ft,Be,e,h);function m(s){const{"onUpdate:expandedNames":p,onUpdateExpandedNames:a,onExpandedNamesChange:t}=e;a&&K(a,s),p&&K(p,s),t&&K(t,s),n.value=s}function r(s){const{onItemHeaderClick:p}=e;p&&K(p,s)}function i(s,p,a){const{accordion:t}=e,{value:A}=y;if(t)s?(m([p]),r({name:p,expanded:!0,event:a})):(m([]),r({name:p,expanded:!1,event:a}));else if(!Array.isArray(A))m([p]),r({name:p,expanded:!0,event:a});else{const C=A.slice(),N=C.findIndex(B=>p===B);~N?(C.splice(N,1),m(C),r({name:p,expanded:!1,event:a})):(C.push(p),m(C),r({name:p,expanded:!0,event:a}))}}Ee(xe,{props:e,mergedClsPrefixRef:h,expandedNamesRef:y,slots:v,toggleItem:i});const c=he("Collapse",d,h),R=D(()=>{const{common:{cubicBezierEaseInOut:s},self:{titleFontWeight:p,dividerColor:a,titlePadding:t,titleTextColor:A,titleTextColorDisabled:C,textColor:N,arrowColor:B,fontSize:z,titleFontSize:g,arrowColorDisabled:I,itemMargin:T}}=x.value;return{"--n-font-size":z,"--n-bezier":s,"--n-text-color":N,"--n-divider-color":a,"--n-title-padding":t,"--n-title-font-size":g,"--n-title-text-color":A,"--n-title-text-color-disabled":C,"--n-title-font-weight":p,"--n-arrow-color":B,"--n-arrow-color-disabled":I,"--n-item-margin":T}}),b=o?me("collapse",void 0,R,e):void 0;return{rtlEnabled:c,mergedTheme:x,mergedClsPrefix:h,cssVars:o?void 0:R,themeClass:b==null?void 0:b.themeClass,onRender:b==null?void 0:b.onRender}},render(){var e;return(e=this.onRender)===null||e===void 0||e.call(this),f("div",{class:[`${this.mergedClsPrefix}-collapse`,this.rtlEnabled&&`${this.mergedClsPrefix}-collapse--rtl`,this.themeClass],style:this.cssVars},this.$slots)}}),mt=q({name:"CollapseItemContent",props:{displayDirective:{type:String,required:!0},show:Boolean,clsPrefix:{type:String,required:!0}},setup(e){return{onceTrue:Ve(ce(e,"show"))}},render(){return f(Pe,null,{default:()=>{const{show:e,displayDirective:v,onceTrue:h,clsPrefix:o}=this,d=v==="show"&&h,n=f("div",{class:`${o}-collapse-item__content-wrapper`},f("div",{class:`${o}-collapse-item__content-inner`},this.$slots));return d?ge(n,[[Fe,e]]):e?n:null}})}}),gt={title:String,name:[String,Number],disabled:Boolean,displayDirective:String},bt=q({name:"CollapseItem",props:gt,setup(e){const{mergedRtlRef:v}=de(e),h=Ue(),o=Ie(()=>{var i;return(i=e.name)!==null&&i!==void 0?i:h}),d=je(xe);d||Te("collapse-item","`n-collapse-item` must be placed inside `n-collapse`.");const{expandedNamesRef:n,props:_,mergedClsPrefixRef:y,slots:x}=d,m=D(()=>{const{value:i}=n;if(Array.isArray(i)){const{value:c}=o;return!~i.findIndex(R=>R===c)}else if(i){const{value:c}=o;return c!==i}return!0});return{rtlEnabled:he("Collapse",v,y),collapseSlots:x,randomName:h,mergedClsPrefix:y,collapsed:m,triggerAreas:ce(_,"triggerAreas"),mergedDisplayDirective:D(()=>{const{displayDirective:i}=e;return i||_.displayDirective}),arrowPlacement:D(()=>_.arrowPlacement),handleClick(i){let c="main";fe(i,"arrow")&&(c="arrow"),fe(i,"extra")&&(c="extra"),_.triggerAreas.includes(c)&&d&&!e.disabled&&d.toggleItem(m.value,o.value,i)}}},render(){const{collapseSlots:e,$slots:v,arrowPlacement:h,collapsed:o,mergedDisplayDirective:d,mergedClsPrefix:n,disabled:_,triggerAreas:y}=this,x=ue(v.header,{collapsed:o},()=>[this.title]),m=v["header-extra"]||e["header-extra"],r=v.arrow||e.arrow;return f("div",{class:[`${n}-collapse-item`,`${n}-collapse-item--${h}-arrow-placement`,_&&`${n}-collapse-item--disabled`,!o&&`${n}-collapse-item--active`,y.map(i=>`${n}-collapse-item--trigger-area-${i}`)]},f("div",{class:[`${n}-collapse-item__header`,!o&&`${n}-collapse-item__header--active`]},f("div",{class:`${n}-collapse-item__header-main`,onClick:this.handleClick},h==="right"&&x,f("div",{class:`${n}-collapse-item-arrow`,key:this.rtlEnabled?0:1,"data-arrow":!0},ue(r,{collapsed:o},()=>[f(Le,{clsPrefix:n},{default:()=>this.rtlEnabled?f(pt,null):f(He,null)})])),h==="left"&&x),De(m,{collapsed:o},i=>f("div",{class:`${n}-collapse-item__header-extra`,onClick:this.handleClick,"data-extra":!0},i))),f(mt,{clsPrefix:n,displayDirective:d,show:!o},v))}});function _t(e){const{primaryColor:v,opacityDisabled:h,borderRadius:o,textColor3:d}=e;return Object.assign(Object.assign({},Oe),{iconColor:d,textColor:"white",loadingColor:v,opacityDisabled:h,railColor:"rgba(0, 0, 0, .14)",railColorActive:v,buttonBoxShadow:"0 1px 4px 0 rgba(0, 0, 0, 0.3), inset 0 0 1px 0 rgba(0, 0, 0, 0.05)",buttonColor:"#FFF",railBorderRadiusSmall:o,railBorderRadiusMedium:o,railBorderRadiusLarge:o,buttonBorderRadiusSmall:o,buttonBorderRadiusMedium:o,buttonBorderRadiusLarge:o,boxShadowFocus:`0 0 0 2px ${We(v,{alpha:.2})}`})}const wt={common:Me,self:_t},xt=E("switch",`
 height: var(--n-height);
 min-width: var(--n-width);
 vertical-align: middle;
 user-select: none;
 -webkit-user-select: none;
 display: inline-flex;
 outline: none;
 justify-content: center;
 align-items: center;
`,[l("children-placeholder",`
 height: var(--n-rail-height);
 display: flex;
 flex-direction: column;
 overflow: hidden;
 pointer-events: none;
 visibility: hidden;
 `),l("rail-placeholder",`
 display: flex;
 flex-wrap: none;
 `),l("button-placeholder",`
 width: calc(1.75 * var(--n-rail-height));
 height: var(--n-rail-height);
 `),E("base-loading",`
 position: absolute;
 top: 50%;
 left: 50%;
 transform: translateX(-50%) translateY(-50%);
 font-size: calc(var(--n-button-width) - 4px);
 color: var(--n-loading-color);
 transition: color .3s var(--n-bezier);
 `,[pe({left:"50%",top:"50%",originalTransform:"translateX(-50%) translateY(-50%)"})]),l("checked, unchecked",`
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 box-sizing: border-box;
 position: absolute;
 white-space: nowrap;
 top: 0;
 bottom: 0;
 display: flex;
 align-items: center;
 line-height: 1;
 `),l("checked",`
 right: 0;
 padding-right: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),l("unchecked",`
 left: 0;
 justify-content: flex-end;
 padding-left: calc(1.25 * var(--n-rail-height) - var(--n-offset));
 `),Y("&:focus",[l("rail",`
 box-shadow: var(--n-box-shadow-focus);
 `)]),$("round",[l("rail","border-radius: calc(var(--n-rail-height) / 2);",[l("button","border-radius: calc(var(--n-button-height) / 2);")])]),ie("disabled",[ie("icon",[$("rubber-band",[$("pressed",[l("rail",[l("button","max-width: var(--n-button-width-pressed);")])]),l("rail",[Y("&:active",[l("button","max-width: var(--n-button-width-pressed);")])]),$("active",[$("pressed",[l("rail",[l("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])]),l("rail",[Y("&:active",[l("button","left: calc(100% - var(--n-offset) - var(--n-button-width-pressed));")])])])])])]),$("active",[l("rail",[l("button","left: calc(100% - var(--n-button-width) - var(--n-offset))")])]),l("rail",`
 overflow: hidden;
 height: var(--n-rail-height);
 min-width: var(--n-rail-width);
 border-radius: var(--n-rail-border-radius);
 cursor: pointer;
 position: relative;
 transition:
 opacity .3s var(--n-bezier),
 background .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 background-color: var(--n-rail-color);
 `,[l("button-icon",`
 color: var(--n-icon-color);
 transition: color .3s var(--n-bezier);
 font-size: calc(var(--n-button-height) - 4px);
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 display: flex;
 justify-content: center;
 align-items: center;
 line-height: 1;
 `,[pe()]),l("button",`
 align-items: center; 
 top: var(--n-offset);
 left: var(--n-offset);
 height: var(--n-button-height);
 width: var(--n-button-width-pressed);
 max-width: var(--n-button-width);
 border-radius: var(--n-button-border-radius);
 background-color: var(--n-button-color);
 box-shadow: var(--n-button-box-shadow);
 box-sizing: border-box;
 cursor: inherit;
 content: "";
 position: absolute;
 transition:
 background-color .3s var(--n-bezier),
 left .3s var(--n-bezier),
 opacity .3s var(--n-bezier),
 max-width .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 `)]),$("active",[l("rail","background-color: var(--n-rail-color-active);")]),$("loading",[l("rail",`
 cursor: wait;
 `)]),$("disabled",[l("rail",`
 cursor: not-allowed;
 opacity: .5;
 `)])]),yt=Object.assign(Object.assign({},ae.props),{size:{type:String,default:"medium"},value:{type:[String,Number,Boolean],default:void 0},loading:Boolean,defaultValue:{type:[String,Number,Boolean],default:!1},disabled:{type:Boolean,default:void 0},round:{type:Boolean,default:!0},"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],checkedValue:{type:[String,Number,Boolean],default:!0},uncheckedValue:{type:[String,Number,Boolean],default:!1},railStyle:Function,rubberBand:{type:Boolean,default:!0},onChange:[Function,Array]});let G;const Ct=q({name:"Switch",props:yt,slots:Object,setup(e){G===void 0&&(typeof CSS<"u"?typeof CSS.supports<"u"?G=CSS.supports("width","max(1px)"):G=!1:G=!0);const{mergedClsPrefixRef:v,inlineThemeDisabled:h}=de(e),o=ae("Switch","-switch",xt,wt,e,v),d=Ye(e),{mergedSizeRef:n,mergedDisabledRef:_}=d,y=k(e.defaultValue),x=ce(e,"value"),m=ve(x,y),r=D(()=>m.value===e.checkedValue),i=k(!1),c=k(!1),R=D(()=>{const{railStyle:g}=e;if(g)return g({focused:c.value,checked:r.value})});function b(g){const{"onUpdate:value":I,onChange:T,onUpdateValue:j}=e,{nTriggerFormInput:X,nTriggerFormChange:Z}=d;I&&K(I,g),j&&K(j,g),T&&K(T,g),y.value=g,X(),Z()}function s(){const{nTriggerFormFocus:g}=d;g()}function p(){const{nTriggerFormBlur:g}=d;g()}function a(){e.loading||_.value||(m.value!==e.checkedValue?b(e.checkedValue):b(e.uncheckedValue))}function t(){c.value=!0,s()}function A(){c.value=!1,p(),i.value=!1}function C(g){e.loading||_.value||g.key===" "&&(m.value!==e.checkedValue?b(e.checkedValue):b(e.uncheckedValue),i.value=!1)}function N(g){e.loading||_.value||g.key===" "&&(g.preventDefault(),i.value=!0)}const B=D(()=>{const{value:g}=n,{self:{opacityDisabled:I,railColor:T,railColorActive:j,buttonBoxShadow:X,buttonColor:Z,boxShadowFocus:S,loadingColor:ye,textColor:Ce,iconColor:ke,[W("buttonHeight",g)]:L,[W("buttonWidth",g)]:Re,[W("buttonWidthPressed",g)]:$e,[W("railHeight",g)]:H,[W("railWidth",g)]:Q,[W("railBorderRadius",g)]:Se,[W("buttonBorderRadius",g)]:Ae},common:{cubicBezierEaseInOut:Ne}}=o.value;let le,ne,oe;return G?(le=`calc((${H} - ${L}) / 2)`,ne=`max(${H}, ${L})`,oe=`max(${Q}, calc(${Q} + ${L} - ${H}))`):(le=se((U(H)-U(L))/2),ne=se(Math.max(U(H),U(L))),oe=U(H)>U(L)?Q:se(U(Q)+U(L)-U(H))),{"--n-bezier":Ne,"--n-button-border-radius":Ae,"--n-button-box-shadow":X,"--n-button-color":Z,"--n-button-width":Re,"--n-button-width-pressed":$e,"--n-button-height":L,"--n-height":ne,"--n-offset":le,"--n-opacity-disabled":I,"--n-rail-border-radius":Se,"--n-rail-color":T,"--n-rail-color-active":j,"--n-rail-height":H,"--n-rail-width":Q,"--n-width":oe,"--n-box-shadow-focus":S,"--n-loading-color":ye,"--n-text-color":Ce,"--n-icon-color":ke}}),z=h?me("switch",D(()=>n.value[0]),B,e):void 0;return{handleClick:a,handleBlur:A,handleFocus:t,handleKeyup:C,handleKeydown:N,mergedRailStyle:R,pressed:i,mergedClsPrefix:v,mergedValue:m,checked:r,mergedDisabled:_,cssVars:h?void 0:B,themeClass:z==null?void 0:z.themeClass,onRender:z==null?void 0:z.onRender}},render(){const{mergedClsPrefix:e,mergedDisabled:v,checked:h,mergedRailStyle:o,onRender:d,$slots:n}=this;d==null||d();const{checked:_,unchecked:y,icon:x,"checked-icon":m,"unchecked-icon":r}=n,i=!(re(x)&&re(m)&&re(r));return f("div",{role:"switch","aria-checked":h,class:[`${e}-switch`,this.themeClass,i&&`${e}-switch--icon`,h&&`${e}-switch--active`,v&&`${e}-switch--disabled`,this.round&&`${e}-switch--round`,this.loading&&`${e}-switch--loading`,this.pressed&&`${e}-switch--pressed`,this.rubberBand&&`${e}-switch--rubber-band`],tabindex:this.mergedDisabled?void 0:0,style:this.cssVars,onClick:this.handleClick,onFocus:this.handleFocus,onBlur:this.handleBlur,onKeyup:this.handleKeyup,onKeydown:this.handleKeydown},f("div",{class:`${e}-switch__rail`,"aria-hidden":"true",style:o},O(_,c=>O(y,R=>c||R?f("div",{"aria-hidden":!0,class:`${e}-switch__children-placeholder`},f("div",{class:`${e}-switch__rail-placeholder`},f("div",{class:`${e}-switch__button-placeholder`}),c),f("div",{class:`${e}-switch__rail-placeholder`},f("div",{class:`${e}-switch__button-placeholder`}),R)):null)),f("div",{class:`${e}-switch__button`},O(x,c=>O(m,R=>O(r,b=>f(Ke,null,{default:()=>this.loading?f(qe,{key:"loading",clsPrefix:e,strokeWidth:20}):this.checked&&(R||c)?f("div",{class:`${e}-switch__button-icon`,key:R?"checked-icon":"icon"},R||c):!this.checked&&(b||c)?f("div",{class:`${e}-switch__button-icon`,key:b?"unchecked-icon":"icon"},b||c):null})))),O(_,c=>c&&f("div",{key:"checked",class:`${e}-switch__checked`},c)),O(y,c=>c&&f("div",{key:"unchecked",class:`${e}-switch__unchecked`},c)))))}}),kt=["disabled"],Rt={class:"gap-3 grid grid-cols-1 sm:grid-cols-2"},$t={key:1,class:"mt-5 space-y-4"},St={class:"gap-4 grid grid-cols-1 sm:grid-cols-3"},At={class:"text-sm text-gray-500"},Nt={class:"text-sm text-gray-500"},Bt={class:"flex gap-3 items-center"},zt=q({__name:"ArEvaluation",setup(e){const v=k(null),h=k([]),o=k("2025-09-01"),d=k("stkcd"),n=k("ym"),_=k("信用评级"),y=k("首次违约日期"),x=k(!1),m=k(""),r=k(null),i=k(!0);Xe([v,o,d,n,_,y],()=>{r.value=null,m.value=""});const c=D(()=>{var a;return((a=r.value)==null?void 0:a.monthly.filter(t=>!i.value||t.valid_AR))||[]});function R(a){return a===null?"无法计算":a.toFixed(6)}const b=[{title:"评级月份",key:"month",width:110},{title:"样本数",key:"N",width:90},{title:"一年内违约数",key:"N_default_1y",width:120},{title:"非违约数",key:"N_nondefault_1y",width:100},{title:"AR值",key:"AR_CAP",width:125,render:a=>R(a.AR_CAP)},{title:"AUC",key:"AUC",width:125,render:a=>R(a.AUC)},{title:"说明",key:"reason",width:220,render:a=>a.valid_AR?"有效":a.reason}];function s(a){var t;h.value=a.fileList,v.value=((t=a.fileList[0])==null?void 0:t.file)||null}async function p(){var t,A;if(m.value="",r.value=null,!v.value){m.value="请先上传评级结果文件";return}if(!o.value||!d.value.trim()||!n.value.trim()||!_.value.trim()||!y.value.trim()){m.value="请填写截止日期和四个字段名称";return}const a=new FormData;a.append("file",v.value),a.append("data_end",o.value),a.append("id_col",d.value.trim()),a.append("date_col",n.value.trim()),a.append("rating_col",_.value.trim()),a.append("default_date_col",y.value.trim()),x.value=!0;try{const C=await _e.post("/ar/calculate",a,{timeout:12e4});if(C.data.status!=="success")throw new Error(C.data.message||"AR计算失败");r.value=C.data.data}catch(C){m.value=((A=(t=C.response)==null?void 0:t.data)==null?void 0:A.message)||C.message||"AR计算失败，请稍后重试"}finally{x.value=!1}}return(a,t)=>{const A=we,C=be,N=ot,B=nt,z=it,g=bt,I=ht,T=lt,j=ut,X=Ct,Z=dt;return M(),J("div",null,[u(A,{type:"info","show-icon":!1,class:"mb-4"},{default:w(()=>t[6]||(t[6]=[F(" 上传主体评级结果即可计算，无需上传模型。总体AR为有效月份AR的等权平均；各月按未来一年内是否首次违约计算。 文件应包含主体代码、评级月份、信用评级、首次违约日期，未违约日期留空。Excel读取第一个工作表。 ")])),_:1}),u(T,{"label-placement":"top"},{default:w(()=>[u(B,{label:"评级结果文件（.xlsx / .csv / .parquet，不超过50MB）"},{default:w(()=>[u(N,{"file-list":h.value,"default-upload":!1,max:1,accept:".xlsx,.csv,.parquet",disabled:x.value,onChange:s},{default:w(()=>[u(C,{disabled:x.value},{default:w(()=>t[7]||(t[7]=[F(" 选择评级结果文件 ")])),_:1},8,["disabled"])]),_:1},8,["file-list","disabled"])]),_:1}),u(B,{label:"违约数据截止日期"},{default:w(()=>[ge(P("input",{"onUpdate:modelValue":t[0]||(t[0]=S=>o.value=S),type:"date",disabled:x.value,class:"px-3 py-2 border rounded dark:bg-gray-800"},null,8,kt),[[Ze,o.value]]),t[8]||(t[8]=P("span",{class:"text-sm text-gray-500 ml-3"},"只纳入具备完整未来一年观察窗口的评级记录。",-1))]),_:1}),u(I,{class:"mb-4"},{default:w(()=>[u(g,{title:"字段设置（文件列名不同时修改）",name:"columns"},{default:w(()=>[P("div",Rt,[u(B,{label:"主体代码列"},{default:w(()=>[u(z,{value:d.value,"onUpdate:value":t[1]||(t[1]=S=>d.value=S),disabled:x.value},null,8,["value","disabled"])]),_:1}),u(B,{label:"评级月份列"},{default:w(()=>[u(z,{value:n.value,"onUpdate:value":t[2]||(t[2]=S=>n.value=S),disabled:x.value},null,8,["value","disabled"])]),_:1}),u(B,{label:"信用评级列"},{default:w(()=>[u(z,{value:_.value,"onUpdate:value":t[3]||(t[3]=S=>_.value=S),disabled:x.value},null,8,["value","disabled"])]),_:1}),u(B,{label:"首次违约日期列"},{default:w(()=>[u(z,{value:y.value,"onUpdate:value":t[4]||(t[4]=S=>y.value=S),disabled:x.value},null,8,["value","disabled"])]),_:1})])]),_:1})]),_:1}),u(C,{type:"primary",loading:x.value,onClick:p},{default:w(()=>t[9]||(t[9]=[F(" 计算AR值 ")])),_:1},8,["loading"])]),_:1}),m.value?(M(),ee(A,{key:0,type:"error",class:"mt-4"},{default:w(()=>[F(V(m.value),1)]),_:1})):te("",!0),r.value?(M(),J("div",$t,[(M(!0),J(Qe,null,Ge(r.value.warnings,S=>(M(),ee(A,{key:S,type:"warning"},{default:w(()=>[F(V(S),1)]),_:2},1024))),128)),P("div",St,[u(j,{label:"总体AR值（有效月份等权平均）",value:R(r.value.summary.overall_ar)},null,8,["value"]),u(j,{label:"有效AR月份数",value:`${r.value.summary.valid_months} / ${r.value.summary.total_months}`},null,8,["value"]),u(j,{label:"有效月份平均AUC",value:R(r.value.summary.mean_auc)},null,8,["value"])]),P("p",At," 截止日期："+V(r.value.summary.data_end)+"；纳入"+V(r.value.summary.subject_count)+"个主体、"+V(r.value.summary.sample_count)+"条主体月度记录。 AR按系数展示，取值范围为-1至1。 ",1),P("p",Nt," 原始"+V(r.value.cleaning.input_rows)+"条；缺失或无效主体/月/评级剔除"+V(r.value.cleaning.missing_rows)+"条； 重复去除"+V(r.value.cleaning.duplicate_rows)+"条；评级时已违约剔除"+V(r.value.cleaning.already_defaulted_rows)+"条； 观察窗口不足一年剔除"+V(r.value.cleaning.incomplete_window_rows)+"条。 ",1),P("div",Bt,[t[10]||(t[10]=P("span",null,"各月AR值",-1)),u(X,{value:i.value,"onUpdate:value":t[5]||(t[5]=S=>i.value=S)},null,8,["value"]),t[11]||(t[11]=P("span",{class:"text-sm text-gray-500"},"仅显示有效月份",-1))]),u(Z,{columns:b,data:c.value,pagination:{pageSize:12},"scroll-x":890,"max-height":420},null,8,["data"])])):te("",!0)])}}}),Et={class:"mx-auto px-4 py-6 max-w-7xl w-full"},Pt={class:"flex gap-2 justify-end"},Lt=q({__name:"new",setup(e){const v=at(),h=k(!1),o=k(!1),d=k(""),n=k(!1),_=k(""),y=k(null);Je().chatSessions.forEach(b=>{b.selected=!1});const x={task_type:"",data_type:"",industry_type:""};async function m(b){d.value="",y.value=b,await r(b)}async function r(b,s=!1){var p,a;h.value=!0;try{s?b.set("force","1"):b.delete("force");const t=await _e.post("/predict",b,{headers:{"Content-Type":"multipart/form-data"}});t.data.status==="success"?v.push(`/result/${t.data.hash}`):t.data.status==="exists"?(_.value=t.data.hash,n.value=!0):d.value=t.data.message||"预测失败，请稍后重试"}catch(t){console.error("Prediction error:",t),d.value=((a=(p=t.response)==null?void 0:p.data)==null?void 0:a.message)||t.message||"预测失败，请稍后重试"}finally{h.value=!1}}function i(){n.value=!1,y.value&&r(y.value,!0)}function c(){n.value=!1,_.value&&v.push(`/result/${_.value}`)}function R(){n.value=!1}return(b,s)=>{const p=be,a=we,t=ct,A=et,C=tt;return M(),J("div",Et,[u(A,{title:"新建预测",bordered:!1,class:"mb-6"},{"header-extra":w(()=>[u(p,{size:"small",secondary:"",onClick:s[0]||(s[0]=N=>o.value=!0)},{default:w(()=>s[3]||(s[3]=[F(" 模型AR值 ")])),_:1})]),default:w(()=>[s[4]||(s[4]=P("p",{class:"text-gray-700 mb-4 dark:text-gray-300"}," 填写预测参数并上传数据文件，系统将自动分析并生成结果。 ",-1)),u(t,{show:h.value},{default:w(()=>[d.value?(M(),ee(a,{key:0,type:"error",class:"mb-4",closable:""},{default:w(()=>[F(V(d.value),1)]),_:1})):te("",!0),u(rt,{data:x,onSubmitSuccess:m})]),_:1},8,["show"])]),_:1}),u(C,{show:o.value,"onUpdate:show":s[1]||(s[1]=N=>o.value=N),preset:"card",title:"模型AR值",style:{width:"1100px","max-width":"95vw"},"content-style":{maxHeight:"80vh",overflowY:"auto"}},{default:w(()=>[o.value?(M(),ee(zt,{key:0})):te("",!0)]),_:1},8,["show"]),u(C,{show:n.value,"onUpdate:show":s[2]||(s[2]=N=>n.value=N),preset:"dialog",title:"结果已存在","positive-text":"重新生成","negative-text":"取消"},{default:w(()=>s[5]||(s[5]=[P("p",null,"检测到相同参数的预测结果已存在，您是否要：",-1)])),action:w(()=>[P("div",Pt,[u(p,{onClick:R},{default:w(()=>s[6]||(s[6]=[F(" 取消 ")])),_:1}),u(p,{type:"info",onClick:c},{default:w(()=>s[7]||(s[7]=[F(" 跳转到已有结果 ")])),_:1}),u(p,{type:"primary",onClick:i},{default:w(()=>s[8]||(s[8]=[F(" 重新生成 ")])),_:1})])]),_:1},8,["show"])])}}});export{Lt as default};
