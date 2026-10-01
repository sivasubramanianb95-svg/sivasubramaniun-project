const form=document.getElementById('comic-form');
if(form){form.addEventListener('submit',()=>{const button=document.getElementById('generate-btn');const status=document.getElementById('status');button.disabled=true;button.textContent='Creating comic…';status.textContent='AI story and panel images are being generated. This can take a while with real models.';});}
