package com.example.calculatortest;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;

public class MainActivity extends Activity {
    private TextView display;
    private double first = 0;
    private String op = "";
    private boolean fresh = true;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        display = findViewById(R.id.display);
        int[] nums = {R.id.b0,R.id.b1,R.id.b2,R.id.b3,R.id.b4,R.id.b5,R.id.b6,R.id.b7,R.id.b8,R.id.b9};
        for (int id : nums) findViewById(id).setOnClickListener(v -> num(((Button)v).getText().toString()));
        findViewById(R.id.bdot).setOnClickListener(v -> num("."));
        int[] ops = {R.id.bplus,R.id.bminus,R.id.bmul,R.id.bdiv};
        for (int id : ops) findViewById(id).setOnClickListener(v -> operate(((Button)v).getText().toString()));
        findViewById(R.id.beq).setOnClickListener(v -> equal());
        findViewById(R.id.bc).setOnClickListener(v -> clear());
        findViewById(R.id.bback).setOnClickListener(v -> backspace());
    }
    private void num(String n) {
        if (fresh || display.getText().toString().equals("0")) { display.setText(n.equals(".") ? "0." : n); fresh=false; }
        else if (n.equals(".") && !display.getText().toString().contains(".")) display.append(".");
        else display.append(n);
    }
    private void operate(String o) { first=Double.parseDouble(display.getText().toString()); op=o; fresh=true; }
    private void equal() {
        if (op.isEmpty()) return;
        double x=Double.parseDouble(display.getText().toString()), r=0;
        if(op.equals("+"))r=first+x; else if(op.equals("−"))r=first-x; else if(op.equals("×"))r=first*x;
        else if(op.equals("÷")){ if(x==0){display.setText("خطأ");op="";fresh=true;return;} r=first/x; }
        display.setText(String.valueOf(r).replaceAll("\\.0$","")); op=""; fresh=true;
    }
    private void clear(){display.setText("0");first=0;op="";fresh=true;}
    private void backspace(){String s=display.getText().toString(); if(s.length()>1)display.setText(s.substring(0,s.length()-1));else display.setText("0");}
}
