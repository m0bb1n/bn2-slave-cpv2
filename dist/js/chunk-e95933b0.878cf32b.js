(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-e95933b0"],{"0fd9":function(t,e,n){"use strict";n("99af"),n("4160"),n("caad"),n("13d5"),n("4ec9"),n("b64b"),n("d3b7"),n("ac1f"),n("2532"),n("3ca3"),n("5319"),n("159b"),n("ddb0");var a=n("ade3"),r=n("5530"),o=(n("4b85"),n("a026")),c=n("d9f7"),i=n("80d2"),l=["sm","md","lg","xl"],s=["start","end","center"];function u(t,e){return l.reduce((function(n,a){return n[t+Object(i["C"])(a)]=e(),n}),{})}var d=function(t){return[].concat(s,["baseline","stretch"]).includes(t)},f=u("align",(function(){return{type:String,default:null,validator:d}})),b=function(t){return[].concat(s,["space-between","space-around"]).includes(t)},v=u("justify",(function(){return{type:String,default:null,validator:b}})),g=function(t){return[].concat(s,["space-between","space-around","stretch"]).includes(t)},p=u("alignContent",(function(){return{type:String,default:null,validator:g}})),h={align:Object.keys(f),justify:Object.keys(v),alignContent:Object.keys(p)},y={align:"align",justify:"justify",alignContent:"align-content"};function m(t,e,n){var a=y[t];if(null!=n){if(e){var r=e.replace(t,"");a+="-".concat(r)}return a+="-".concat(n),a.toLowerCase()}}var j=new Map;e["a"]=o["a"].extend({name:"v-row",functional:!0,props:Object(r["a"])({tag:{type:String,default:"div"},dense:Boolean,noGutters:Boolean,align:{type:String,default:null,validator:d}},f,{justify:{type:String,default:null,validator:b}},v,{alignContent:{type:String,default:null,validator:g}},p),render:function(t,e){var n=e.props,r=e.data,o=e.children,i="";for(var l in n)i+=String(n[l]);var s=j.get(i);return s||function(){var t,e;for(e in s=[],h)h[e].forEach((function(t){var a=n[t],r=m(e,t,a);r&&s.push(r)}));s.push((t={"no-gutters":n.noGutters,"row--dense":n.dense},Object(a["a"])(t,"align-".concat(n.align),n.align),Object(a["a"])(t,"justify-".concat(n.justify),n.justify),Object(a["a"])(t,"align-content-".concat(n.alignContent),n.alignContent),t)),j.set(i,s)}(),t(n.tag,Object(c["a"])(r,{staticClass:"row",class:s}),o)}})},"4b85":function(t,e,n){},"62ad":function(t,e,n){"use strict";n("4160"),n("caad"),n("13d5"),n("45fc"),n("4ec9"),n("a9e3"),n("b64b"),n("d3b7"),n("ac1f"),n("3ca3"),n("5319"),n("2ca0"),n("159b"),n("ddb0");var a=n("ade3"),r=n("5530"),o=(n("4b85"),n("a026")),c=n("d9f7"),i=n("80d2"),l=["sm","md","lg","xl"],s=function(){return l.reduce((function(t,e){return t[e]={type:[Boolean,String,Number],default:!1},t}),{})}(),u=function(){return l.reduce((function(t,e){return t["offset"+Object(i["C"])(e)]={type:[String,Number],default:null},t}),{})}(),d=function(){return l.reduce((function(t,e){return t["order"+Object(i["C"])(e)]={type:[String,Number],default:null},t}),{})}(),f={col:Object.keys(s),offset:Object.keys(u),order:Object.keys(d)};function b(t,e,n){var a=t;if(null!=n&&!1!==n){if(e){var r=e.replace(t,"");a+="-".concat(r)}return"col"!==t||""!==n&&!0!==n?(a+="-".concat(n),a.toLowerCase()):a.toLowerCase()}}var v=new Map;e["a"]=o["a"].extend({name:"v-col",functional:!0,props:Object(r["a"])({cols:{type:[Boolean,String,Number],default:!1}},s,{offset:{type:[String,Number],default:null}},u,{order:{type:[String,Number],default:null}},d,{alignSelf:{type:String,default:null,validator:function(t){return["auto","start","end","center","baseline","stretch"].includes(t)}},tag:{type:String,default:"div"}}),render:function(t,e){var n=e.props,r=e.data,o=e.children,i=(e.parent,"");for(var l in n)i+=String(n[l]);var s=v.get(i);return s||function(){var t,e;for(e in s=[],f)f[e].forEach((function(t){var a=n[t],r=b(e,t,a);r&&s.push(r)}));var r=s.some((function(t){return t.startsWith("col-")}));s.push((t={col:!r||!n.cols},Object(a["a"])(t,"col-".concat(n.cols),n.cols),Object(a["a"])(t,"offset-".concat(n.offset),n.offset),Object(a["a"])(t,"order-".concat(n.order),n.order),Object(a["a"])(t,"align-self-".concat(n.alignSelf),n.alignSelf),t)),v.set(i,s)}(),t(n.tag,Object(c["a"])(r,{class:s}),o)}})},"90a2":function(t,e,n){"use strict";n("7db0");var a=n("53ca");function r(t,e){var n=e.modifiers||{},r=e.value,c="object"===Object(a["a"])(r)?r:{handler:r,options:{}},i=c.handler,l=c.options,s=new IntersectionObserver((function(){var e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:[],a=arguments.length>1?arguments[1]:void 0;if(t._observe){if(i&&(!n.quiet||t._observe.init)){var r=Boolean(e.find((function(t){return t.isIntersecting})));i(e,a,r)}t._observe.init&&n.once?o(t):t._observe.init=!0}}),l);t._observe={init:!1,observer:s},s.observe(t)}function o(t){t._observe&&(t._observe.observer.unobserve(t),delete t._observe)}var c={inserted:r,unbind:o};e["a"]=c},a523:function(t,e,n){"use strict";n("99af"),n("4de4"),n("b64b"),n("2ca0"),n("20f6"),n("4b85");var a=n("e8f2"),r=n("d9f7");e["a"]=Object(a["a"])("container").extend({name:"v-container",functional:!0,props:{id:String,tag:{type:String,default:"div"},fluid:{type:Boolean,default:!1}},render:function(t,e){var n,a=e.props,o=e.data,c=e.children,i=o.attrs;return i&&(o.attrs={},n=Object.keys(i).filter((function(t){if("slot"===t)return!1;var e=i[t];return t.startsWith("data-")?(o.attrs[t]=e,!1):e||"string"===typeof e}))),a.id&&(o.domProps=o.domProps||{},o.domProps.id=a.id),t(a.tag,Object(r["a"])(o,{staticClass:"container",class:Array({"container--fluid":a.fluid}).concat(n||[])}),c)}})},a722:function(t,e,n){"use strict";n("20f6");var a=n("e8f2");e["a"]=Object(a["a"])("layout")},bb51:function(t,e,n){"use strict";n.r(e);var a=function(){var t=this,e=t.$createElement,a=t._self._c||e;return a("div",{staticClass:"home"},[a("img",{attrs:{alt:"Vue logo",src:n("cf05")}}),a("HelloWorld",{attrs:{msg:"Welcome to Your Vue.js App"}})],1)},r=[],o=n("fdab"),c={name:"Home",components:{HelloWorld:o["a"]}},i=c,l=n("2877"),s=Object(l["a"])(i,a,r,!1,null,null,null);e["default"]=s.exports},cf05:function(t,e,n){t.exports=n.p+"img/logo.82b9c7a5.png"},e8f2:function(t,e,n){"use strict";n.d(e,"a",(function(){return r}));n("99af"),n("4de4"),n("a15b"),n("b64b"),n("2ca0"),n("498a");var a=n("a026");function r(t){return a["a"].extend({name:"v-".concat(t),functional:!0,props:{id:String,tag:{type:String,default:"div"}},render:function(e,n){var a=n.props,r=n.data,o=n.children;r.staticClass="".concat(t," ").concat(r.staticClass||"").trim();var c=r.attrs;if(c){r.attrs={};var i=Object.keys(c).filter((function(t){if("slot"===t)return!1;var e=c[t];return t.startsWith("data-")?(r.attrs[t]=e,!1):e||"string"===typeof e}));i.length&&(r.staticClass+=" ".concat(i.join(" ")))}return a.id&&(r.domProps=r.domProps||{},r.domProps.id=a.id),e(a.tag,r,o)}})}},fdab:function(t,e,n){"use strict";var a=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("v-container",[n("v-layout",[n("v-sheet",[n("v-row",[n("v-col",{attrs:{cols:"6"}},[n("v-text-field",{attrs:{label:"Watch min(s)"},model:{value:t.watch_length,callback:function(e){t.watch_length=e},expression:"watch_length"}})],1),n("v-col",[n("v-btn",{attrs:{disabled:t.btn_delay,text:"",color:"primary"},on:{click:function(e){t.stopViewers(),t.btn_clicked()}}},[t._v("EDIT")])],1)],1),n("v-btn",{attrs:{disabled:t.btn_delay,text:"",color:"error"},on:{click:function(e){t.stopViewers(),t.btn_clicked()}}},[t._v("STOP")])],1)],1)],1)},r=[],o={data:function(){return{watch_length:null,tracker_tag:null,btn_delay:!1}},methods:{btn_clicked:function(){this.btn_delay=!0;var t=this;setTimeout((function(){t.btn_delay=!1}),1500)},createTrackerEvent:function(t){var e=arguments.length>1&&void 0!==arguments[1]?arguments[1]:{};return{route:"bd.@md.tag.send",data:{tag:this.tracker_tag,data:{event:t,payload:e}}}},editViewerMins:function(){var t=this.createTrackerEvent("EDIT",{watch_length:this.watch_length}),e=this.$socket.emit("redirect",t);e.connected&&console.log("SENT EDIT VIEWER MINS")},stopViewers:function(){var t=this.createTrackerEvent("STOP"),e=this.$socket.emit("redirect",t);e.connected&&console.log("SENT STOP VIEWERS")}}},c=o,i=n("2877"),l=n("6544"),s=n.n(l),u=n("8336"),d=n("62ad"),f=n("a523"),b=n("a722"),v=n("0fd9"),g=n("8dd9"),p=n("8654"),h=Object(i["a"])(c,a,r,!1,null,null,null);e["a"]=h.exports;s()(h,{VBtn:u["a"],VCol:d["a"],VContainer:f["a"],VLayout:b["a"],VRow:v["a"],VSheet:g["a"],VTextField:p["a"]})}}]);