const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('relay',{
 connectGoogle:()=>ipcRenderer.invoke('relay:connect'),
 request:(path,method='GET',body)=>ipcRenderer.invoke('relay:request',path,method,body),
 importFile:()=>ipcRenderer.invoke('relay:import'),
 notify:(title,body)=>ipcRenderer.invoke('relay:notify',title,body),
 openExternal:url=>ipcRenderer.invoke('relay:external',url),
 saveSnapshot:data=>ipcRenderer.invoke('relay:cache-save',data),
 loadSnapshot:()=>ipcRenderer.invoke('relay:cache-load'),
 version:()=>ipcRenderer.invoke('relay:version'),
 watchFolder:()=>ipcRenderer.invoke('relay:watch'),
 onFiles:cb=>{const listener=(_,files)=>cb(files);ipcRenderer.on('relay:files',listener);return()=>ipcRenderer.removeListener('relay:files',listener)}
});
