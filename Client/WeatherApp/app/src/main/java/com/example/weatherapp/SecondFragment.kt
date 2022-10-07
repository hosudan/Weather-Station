package com.example.weatherapp

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import androidx.navigation.fragment.findNavController
import com.bumptech.glide.Glide
import com.example.weatherapp.databinding.FragmentSecondBinding


/**
 * A simple [Fragment] subclass as the second destination in the navigation.
 */
class SecondFragment() : Fragment() {

    private var _binding: FragmentSecondBinding? = null
    var urls : String? = ""

    // This property is only valid between onCreateView and
    // onDestroyView.
    private val binding get() = _binding!!

    private lateinit var bm : LocalBroadcastManager

    override fun onAttach(context: Context) {
        super.onAttach(context)
        bm = LocalBroadcastManager.getInstance(context) /// gucci?
        val actionReceiver = IntentFilter()
        actionReceiver.addAction("newMessageArrived")
        bm.registerReceiver(onMessageReceived, actionReceiver)
    }


    private var onMessageReceived = object: BroadcastReceiver() {
        override fun onReceive(context: Context,intent: Intent) {
            if (intent != null) {
                val msg = intent.getStringExtra("message")
                if (msg != null) {
                    downloadViaURL(msg)
                }
            }
        }
    }

    override fun onDetach() {
        super.onDetach();
        bm.unregisterReceiver(onMessageReceived);
    }


    fun downloadViaURL(location:String){
        _binding?.let {
            Glide.with(this).load(location).error(R.drawable.ic_launcher_background).into(
                it.imageView2)
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        _binding = FragmentSecondBinding.inflate(inflater, container, false)
        this.urls = arguments?.getString("link")
        this.urls?.let { downloadViaURL(it) }
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.buttonSecond.setOnClickListener {
            findNavController().navigate(R.id.action_SecondFragment_to_FirstFragment)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}