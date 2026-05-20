// function showStep2() {
//     document.getElementById('step1').style.display = 'none';
//     document.getElementById('step2').style.display = 'block';
// }

function showStep2() {
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'block';
    document.getElementById('leftImage').style.display = 'none';
    document.getElementById('signupHeading').style.display = 'none';
    // document.querySelector('.right').style.marginTop = '-170';

}

function showStep3() {
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'block';
    document.getElementById('signupHeading').style.display = 'none';

}

function showStep4() {
    document.getElementById('step3').style.display = 'none';
    document.getElementById('step4').style.display = 'block';
    document.getElementById('signupHeading').style.display = 'none';

}

function showStep5() {
    document.getElementById('step4').style.display = 'none';
    document.getElementById('step5').style.display = 'block';
    document.getElementById('signupHeading').style.display = 'none';

}

function showStep6() {
    document.getElementById('step5').style.display = 'none';
    document.getElementById('step6').style.display = 'block';
    document.getElementById('signupHeading').style.display = 'none';

}

function editStudent(studentId) {
    // Implement edit functionality
    alert('Edit student ' + studentId);
}

function deleteStudent(studentId) {
    // Implement delete functionality
    alert('Delete student ' + studentId);
}
