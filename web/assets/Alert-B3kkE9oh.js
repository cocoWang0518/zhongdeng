import{v as N,b9 as V,ba as v,a8 as C,x as E,aY as Y,y as x,A as g,z as T,d as G,k as a,aN as J,aP as K,I as X,J as q,Y as Q,C as U,E as B,X as Z,e as H,aS as D,ae as f,G as ee,r as oe,N as re,az as ne,W as te,ay as se,aA as ie}from"./index-zztOTcjm.js";function le(r){const{lineHeight:e,borderRadius:s,fontWeightStrong:l,baseColor:t,dividerColor:u,actionColor:I,textColor1:d,textColor2:n,closeColorHover:c,closeColorPressed:p,closeIconColor:m,closeIconColorHover:$,closeIconColorPressed:i,infoColor:o,successColor:z,warningColor:S,errorColor:y,fontSize:P}=r;return Object.assign(Object.assign({},V),{fontSize:P,lineHeight:e,titleFontWeight:l,borderRadius:s,border:`1px solid ${u}`,color:I,titleTextColor:d,iconColor:n,contentTextColor:n,closeBorderRadius:s,closeColorHover:c,closeColorPressed:p,closeIconColor:m,closeIconColorHover:$,closeIconColorPressed:i,borderInfo:`1px solid ${v(t,C(o,{alpha:.25}))}`,colorInfo:v(t,C(o,{alpha:.08})),titleTextColorInfo:d,iconColorInfo:o,contentTextColorInfo:n,closeColorHoverInfo:c,closeColorPressedInfo:p,closeIconColorInfo:m,closeIconColorHoverInfo:$,closeIconColorPressedInfo:i,borderSuccess:`1px solid ${v(t,C(z,{alpha:.25}))}`,colorSuccess:v(t,C(z,{alpha:.08})),titleTextColorSuccess:d,iconColorSuccess:z,contentTextColorSuccess:n,closeColorHoverSuccess:c,closeColorPressedSuccess:p,closeIconColorSuccess:m,closeIconColorHoverSuccess:$,closeIconColorPressedSuccess:i,borderWarning:`1px solid ${v(t,C(S,{alpha:.33}))}`,colorWarning:v(t,C(S,{alpha:.08})),titleTextColorWarning:d,iconColorWarning:S,contentTextColorWarning:n,closeColorHoverWarning:c,closeColorPressedWarning:p,closeIconColorWarning:m,closeIconColorHoverWarning:$,closeIconColorPressedWarning:i,borderError:`1px solid ${v(t,C(y,{alpha:.25}))}`,colorError:v(t,C(y,{alpha:.08})),titleTextColorError:d,iconColorError:y,contentTextColorError:n,closeColorHoverError:c,closeColorPressedError:p,closeIconColorError:m,closeIconColorHoverError:$,closeIconColorPressedError:i})}const ae={common:N,self:le},{cubicBezierEaseInOut:b,cubicBezierEaseOut:ce,cubicBezierEaseIn:de}=Y;function ge({overflow:r="hidden",duration:e=".3s",originalTransition:s="",leavingDelay:l="0s",foldPadding:t=!1,enterToProps:u=void 0,leaveToProps:I=void 0,reverse:d=!1}={}){const n=d?"leave":"enter",c=d?"enter":"leave";return[E(`&.fade-in-height-expand-transition-${c}-from,
 &.fade-in-height-expand-transition-${n}-to`,Object.assign(Object.assign({},u),{opacity:1})),E(`&.fade-in-height-expand-transition-${c}-to,
 &.fade-in-height-expand-transition-${n}-from`,Object.assign(Object.assign({},I),{opacity:0,marginTop:"0 !important",marginBottom:"0 !important",paddingTop:t?"0 !important":void 0,paddingBottom:t?"0 !important":void 0})),E(`&.fade-in-height-expand-transition-${c}-active`,`
 overflow: ${r};
 transition:
 max-height ${e} ${b} ${l},
 opacity ${e} ${ce} ${l},
 margin-top ${e} ${b} ${l},
 margin-bottom ${e} ${b} ${l},
 padding-top ${e} ${b} ${l},
 padding-bottom ${e} ${b} ${l}
 ${s?`,${s}`:""}
 `),E(`&.fade-in-height-expand-transition-${n}-active`,`
 overflow: ${r};
 transition:
 max-height ${e} ${b},
 opacity ${e} ${de},
 margin-top ${e} ${b},
 margin-bottom ${e} ${b},
 padding-top ${e} ${b},
 padding-bottom ${e} ${b}
 ${s?`,${s}`:""}
 `)]}const he=x("alert",`
 line-height: var(--n-line-height);
 border-radius: var(--n-border-radius);
 position: relative;
 transition: background-color .3s var(--n-bezier);
 background-color: var(--n-color);
 text-align: start;
 word-break: break-word;
`,[g("border",`
 border-radius: inherit;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 transition: border-color .3s var(--n-bezier);
 border: var(--n-border);
 pointer-events: none;
 `),T("closable",[x("alert-body",[g("title",`
 padding-right: 24px;
 `)])]),g("icon",{color:"var(--n-icon-color)"}),x("alert-body",{padding:"var(--n-padding)"},[g("title",{color:"var(--n-title-text-color)"}),g("content",{color:"var(--n-content-text-color)"})]),ge({originalTransition:"transform .3s var(--n-bezier)",enterToProps:{transform:"scale(1)"},leaveToProps:{transform:"scale(0.9)"}}),g("icon",`
 position: absolute;
 left: 0;
 top: 0;
 align-items: center;
 justify-content: center;
 display: flex;
 width: var(--n-icon-size);
 height: var(--n-icon-size);
 font-size: var(--n-icon-size);
 margin: var(--n-icon-margin);
 `),g("close",`
 transition:
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 position: absolute;
 right: 0;
 top: 0;
 margin: var(--n-close-margin);
 `),T("show-icon",[x("alert-body",{paddingLeft:"calc(var(--n-icon-margin-left) + var(--n-icon-size) + var(--n-icon-margin-right))"})]),T("right-adjust",[x("alert-body",{paddingRight:"calc(var(--n-close-size) + var(--n-padding) + 2px)"})]),x("alert-body",`
 border-radius: var(--n-border-radius);
 transition: border-color .3s var(--n-bezier);
 `,[g("title",`
 transition: color .3s var(--n-bezier);
 font-size: 16px;
 line-height: 19px;
 font-weight: var(--n-title-font-weight);
 `,[E("& +",[g("content",{marginTop:"9px"})])]),g("content",{transition:"color .3s var(--n-bezier)",fontSize:"var(--n-font-size)"})]),g("icon",{transition:"color .3s var(--n-bezier)"})]),fe=Object.assign(Object.assign({},B.props),{title:String,showIcon:{type:Boolean,default:!0},type:{type:String,default:"default"},bordered:{type:Boolean,default:!0},closable:Boolean,onClose:Function,onAfterLeave:Function,onAfterHide:Function}),ue=G({name:"Alert",inheritAttrs:!1,props:fe,slots:Object,setup(r){const{mergedClsPrefixRef:e,mergedBorderedRef:s,inlineThemeDisabled:l,mergedRtlRef:t}=U(r),u=B("Alert","-alert",he,ae,r,e),I=Z("Alert",t,e),d=H(()=>{const{common:{cubicBezierEaseInOut:i},self:o}=u.value,{fontSize:z,borderRadius:S,titleFontWeight:y,lineHeight:P,iconSize:_,iconMargin:R,iconMarginRtl:W,closeIconSize:w,closeBorderRadius:A,closeSize:j,closeMargin:O,closeMarginRtl:k,padding:L}=o,{type:h}=r,{left:F,right:M}=D(R);return{"--n-bezier":i,"--n-color":o[f("color",h)],"--n-close-icon-size":w,"--n-close-border-radius":A,"--n-close-color-hover":o[f("closeColorHover",h)],"--n-close-color-pressed":o[f("closeColorPressed",h)],"--n-close-icon-color":o[f("closeIconColor",h)],"--n-close-icon-color-hover":o[f("closeIconColorHover",h)],"--n-close-icon-color-pressed":o[f("closeIconColorPressed",h)],"--n-icon-color":o[f("iconColor",h)],"--n-border":o[f("border",h)],"--n-title-text-color":o[f("titleTextColor",h)],"--n-content-text-color":o[f("contentTextColor",h)],"--n-line-height":P,"--n-border-radius":S,"--n-font-size":z,"--n-title-font-weight":y,"--n-icon-size":_,"--n-icon-margin":R,"--n-icon-margin-rtl":W,"--n-close-size":j,"--n-close-margin":O,"--n-close-margin-rtl":k,"--n-padding":L,"--n-icon-margin-left":F,"--n-icon-margin-right":M}}),n=l?ee("alert",H(()=>r.type[0]),d,r):void 0,c=oe(!0),p=()=>{const{onAfterLeave:i,onAfterHide:o}=r;i&&i(),o&&o()};return{rtlEnabled:I,mergedClsPrefix:e,mergedBordered:s,visible:c,handleCloseClick:()=>{var i;Promise.resolve((i=r.onClose)===null||i===void 0?void 0:i.call(r)).then(o=>{o!==!1&&(c.value=!1)})},handleAfterLeave:()=>{p()},mergedTheme:u,cssVars:l?void 0:d,themeClass:n==null?void 0:n.themeClass,onRender:n==null?void 0:n.onRender}},render(){var r;return(r=this.onRender)===null||r===void 0||r.call(this),a(Q,{onAfterLeave:this.handleAfterLeave},{default:()=>{const{mergedClsPrefix:e,$slots:s}=this,l={class:[`${e}-alert`,this.themeClass,this.closable&&`${e}-alert--closable`,this.showIcon&&`${e}-alert--show-icon`,!this.title&&this.closable&&`${e}-alert--right-adjust`,this.rtlEnabled&&`${e}-alert--rtl`],style:this.cssVars,role:"alert"};return this.visible?a("div",Object.assign({},J(this.$attrs,l)),this.closable&&a(K,{clsPrefix:e,class:`${e}-alert__close`,onClick:this.handleCloseClick}),this.bordered&&a("div",{class:`${e}-alert__border`}),this.showIcon&&a("div",{class:`${e}-alert__icon`,"aria-hidden":"true"},X(s.icon,()=>[a(re,{clsPrefix:e},{default:()=>{switch(this.type){case"success":return a(ie,null);case"info":return a(se,null);case"warning":return a(te,null);case"error":return a(ne,null);default:return null}}})])),a("div",{class:[`${e}-alert-body`,this.mergedBordered&&`${e}-alert-body--bordered`]},q(s.header,t=>{const u=t||this.title;return u?a("div",{class:`${e}-alert-body__title`},u):null}),s.default&&a("div",{class:`${e}-alert-body__content`},s))):null}})}});export{ue as _,ge as f};
