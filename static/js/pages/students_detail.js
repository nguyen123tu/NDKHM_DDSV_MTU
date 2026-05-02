async function trainSingle(mssv) {
    if(!confirm("Bạn muốn yêu cầu AI quét lại hình ảnh của sinh viên này để học dữ liệu khuôn mặt?")) return;
    
    try {
        const res = await fetch(`/training/student/${mssv}`, {method: 'POST'});
        const data = await res.json();
        
        if(data.success) {
            alert('Quá trình học sinh viên này đã hoàn tất!');
            window.location.reload();
        } else {
            alert('Lỗi: ' + data.msg);
        }
    } catch(err) {
        alert('Server đang quá tải không thể phản hồi yêu cầu Neural Network lúc này!');
    }
}