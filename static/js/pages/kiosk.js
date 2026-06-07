// Clock
        function updateClock(){
            document.getElementById('clock').innerText = new Date().toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
        }
        setInterval(updateClock,1000); updateClock();

        // Camera
        const video=document.getElementById('webcam'), canvas=document.getElementById('canvas-capture'), ctx=canvas.getContext('2d');
        async function setupCamera(){
            try{
                // Thử khởi động với độ phân giải HD
                const stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:1280},height:{ideal:720}},audio:false});
                video.srcObject=stream;
            }catch(err){
                console.error("Cam Error:",err);
                if(err.name==='NotAllowedError') {
                    alert("Cần cấp quyền Camera cho trình duyệt!");
                } else {
                    // Thử lại với độ phân giải mặc định của thiết bị nếu bị lỗi (như AbortError / Timeout)
                    console.log("Thử lại với cấu hình Camera mặc định...");
                    try {
                        const fallbackStream = await navigator.mediaDevices.getUserMedia({video: true, audio: false});
                        video.srcObject = fallbackStream;
                    } catch(fallbackErr) {
                        console.error("Fallback Cam Error:", fallbackErr);
                        alert("Không thể khởi động Camera. Vui lòng kiểm tra xem có ứng dụng khác đang sử dụng Camera không (Zalo, Zoom...) hoặc cắm lại cáp USB.");
                    }
                }
            }
        }

        let isProcessing=false, lastMssv=null, lastTime=0;
        async function captureAndRecognize(){
            if(isProcessing||video.videoWidth===0) return;
            const lopSelect = document.getElementById('kiosk-lop-id');
            const lopId = lopSelect ? lopSelect.value : '';
            canvas.width=video.videoWidth; canvas.height=video.videoHeight;
            ctx.drawImage(video,0,0,canvas.width,canvas.height);
            const dataUrl=canvas.toDataURL('image/jpeg',0.6);
            isProcessing=true;
            try{
                const body = {image: dataUrl};
                if(lopId) body.lop_id = parseInt(lopId);
                const res=await fetch('/public/api/recognize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
                if(!res.ok) throw new Error("Server error");
                const d=await res.json();
                if(d.success){
                    const now=Date.now();
                    if(d.student.mssv!==lastMssv||(now-lastTime>10000)){
                        showResult(d); lastMssv=d.student.mssv; lastTime=now;
                    }
                }
            }catch(e){console.error("API:",e)}
            finally{setTimeout(()=>{isProcessing=false},2000)}
        }

        function showResult(data){
            const p=document.getElementById('result-panel'), s=data.student, a=data.attendance;
            document.getElementById('res-name').innerText=s.ho_ten;
            document.getElementById('res-mssv').innerText=`MSSV: ${s.mssv}`;
            document.getElementById('res-avatar').src=s.avatar?`/${s.avatar}`:'/static/img/truong-xay-dung-mien-tay.jpg';
            document.getElementById('res-msg').innerText=a?(a.msg||"Điểm danh hoàn tất"):"Nhận diện thành công";
            try{new Audio('https://assets.mixkit.co/active_storage/sfx/2568/2568-preview.mp3').play()}catch(e){}
            p.style.display='block';
            addLog(s);
            setTimeout(()=>{p.style.display='none'},5000);
        }

        function addLog(s){
            const c=document.getElementById('log-container');
            const t=new Date().toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit'});
            const item=document.createElement('div');
            item.className='log-item';
            item.innerHTML=`<span class="log-time">${t}</span><div class="flex-grow-1"><div class="log-name">${s.ho_ten}</div><div class="log-mssv">${s.mssv}</div></div><span class="log-check"><i class="fas fa-check-circle"></i></span>`;
            if(c.children[0]&&c.children[0].classList.contains('text-center')) c.innerHTML='';
            c.prepend(item);
            if(c.children.length>15) c.removeChild(c.lastChild);
            const sc=document.getElementById('stat-count');
            sc.innerText=parseInt(sc.innerText)+1;
        }

        setupCamera().then(()=>{setInterval(captureAndRecognize,2000)});