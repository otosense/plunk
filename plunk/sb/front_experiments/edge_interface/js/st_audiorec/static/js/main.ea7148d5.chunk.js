(this.webpackJsonpstreamlit_component_template=this.webpackJsonpstreamlit_component_template||[]).push([[0],{17:function(e,t,a){e.exports=a(28)},28:function(e,t,a){"use strict";a.r(t);var o=a(6),n=a.n(o),r=a(15),i=a.n(r),c=a(0),l=a(1),s=a(2),d=a(3),u=a(8),p=a(11),m=(a(27),function(e){Object(s.a)(a,e);var t=Object(d.a)(a);function a(){var e;Object(l.a)(this,a);for(var o=arguments.length,r=new Array(o),i=0;i<o;i++)r[i]=arguments[i];return(e=t.call.apply(t,[this].concat(r))).state={isFocused:!1,recordState:null,audioDataURL:"",reset:!1},e.render=function(){var t=e.props.theme,a={},o=e.state,r=o.recordState,i=o.audioDataURL;if(t){var c="1px solid ".concat(e.state.isFocused?t.primaryColor:"gray");a.border=c,a.outline=c}return n.a.createElement("span",null,n.a.createElement("div",null,n.a.createElement("button",{id:"record",onClick:e.onClick_start,disabled:e.isRecording()},"Start Recording"),n.a.createElement("button",{id:"stop",onClick:e.onClick_stop,disabled:!e.isRecording()},"Stop"),n.a.createElement("button",{id:"reset",onClick:e.onClick_reset,disabled:e.isRecording()||!i},"Reset"),n.a.createElement("button",{id:"continue",onClick:e.onClick_continue,disabled:e.isRecording()||!i},"Download"),n.a.createElement(p.b,{state:r,onStop:e.onStop_audio,type:"audio/wav",backgroundColor:"rgb(255, 255, 255)",foregroundColor:"rgb(255,76,75)",canvasWidth:450,canvasHeight:100}),n.a.createElement("audio",{id:"audio",controls:!0,src:i})))},e.isRecording=function(){return e.state.recordState==p.a.START},e.onClick_start=function(){e.setState({reset:!1,audioDataURL:"",recordState:p.a.START}),u.a.setComponentValue("")},e.onClick_stop=function(){e.setState({reset:!1,recordState:p.a.STOP})},e.onClick_reset=function(){e.setState({reset:!0,audioDataURL:"",recordState:p.a.STOP}),u.a.setComponentValue("")},e.onClick_continue=function(){if(""!==e.state.audioDataURL){var t=(new Date).toLocaleString(),a="streamlit_audio_"+(t=(t=(t=t.replace(" ","")).replace(/_/g,"")).replace(",",""))+".wav",o=document.createElement("a");o.style.display="none",o.href=e.state.audioDataURL,o.download=a,document.body.appendChild(o),o.click()}},e.onStop_audio=function(t){!0===e.state.reset?(e.setState({audioDataURL:""}),u.a.setComponentValue("")):(e.setState({audioDataURL:t.url}),u.a.setComponentValue(t.url))},e}return Object(c.a)(a)}(u.b)),b=Object(u.c)(m);u.a.setComponentReady(),u.a.setFrameHeight(),i.a.render(n.a.createElement(n.a.StrictMode,null,n.a.createElement(b,null)),document.getElementById("root"))}},[[17,1,2]]]);
//# sourceMappingURL=main.ea7148d5.chunk.js.map