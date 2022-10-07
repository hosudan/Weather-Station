package com.example.weatherapp

import android.content.Context
import android.os.AsyncTask
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.example.weatherapp.databinding.FragmentFirstBinding
import com.google.firebase.iid.FirebaseInstanceId
import java.io.OutputStreamWriter
import java.io.PrintWriter
import java.net.Socket
import java.util.*
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors


/**
 * A simple [Fragment] subclass as the default destination in the navigation.
 */
class FirstFragment : Fragment() {

    private var _binding: FragmentFirstBinding? = null
    val SERVER_IP = "192.168.0.127" // The SERVER_IP must be the same in server and client
    val PORT = 1234 // You can put any arbitrary PORT value


    // This property is only valid between onCreateView and
    // onDestroyView.
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {

        _binding = FragmentFirstBinding.inflate(inflater, container, false)
        return binding.root

    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.buttonFirst.setOnClickListener {
            findNavController().navigate(R.id.action_FirstFragment_to_SecondFragment)
        }
        binding.buttonGetphoto.setOnClickListener(){
            binding.textviewResult.text = "Waiting server reply"
            val executor: ExecutorService = Executors.newSingleThreadExecutor()
            val handler = Handler(Looper.getMainLooper())

            executor.execute {
                try {
                    val socket = Socket(SERVER_IP, PORT) //Server IP and PORT
                    val sc = Scanner(socket.getInputStream())
                    val printWriter = PrintWriter(OutputStreamWriter(socket.getOutputStream()))
                    printWriter.write(""+FirebaseInstanceId.getInstance().getToken()+" sendphoto") // Send Data
                    printWriter.flush()
                    binding.textviewResult.text= sc.next()
                } catch (e: Exception) {
                    Log.d("Exception", e.toString())
                    }
                handler.post {
                }
            }
        }
        binding.buttonStart.setOnClickListener(){
            binding.textviewResult.text = "Waiting server reply"
            val executor: ExecutorService = Executors.newSingleThreadExecutor()
            val handler = Handler(Looper.getMainLooper())

            executor.execute {
                try {
                    val socket = Socket(SERVER_IP, PORT) //Server IP and PORT
                    val sc = Scanner(socket.getInputStream())
                    val printWriter = PrintWriter(OutputStreamWriter(socket.getOutputStream()))
                    printWriter.write(""+FirebaseInstanceId.getInstance().getToken()+" statistics") // Send Data
                    printWriter.flush()
                    binding.textviewResult.text= sc.next()
                } catch (e: Exception) {
                    Log.d("Exception", e.toString())
                }
                handler.post {
                }
            }
        }
        binding.buttonStop.setOnClickListener(){
            binding.textviewResult.text = "Waiting server reply"
            val executor: ExecutorService = Executors.newSingleThreadExecutor()
            val handler = Handler(Looper.getMainLooper())

            executor.execute {
                try {
                    val socket = Socket(SERVER_IP, PORT) //Server IP and PORT
                    val sc = Scanner(socket.getInputStream())
                    val printWriter = PrintWriter(OutputStreamWriter(socket.getOutputStream()))
                    printWriter.write(""+FirebaseInstanceId.getInstance().getToken()+" statistics") // Send Data
                    printWriter.flush()
                    binding.textviewResult.text= sc.next()
                } catch (e: Exception) {
                    Log.d("Exception", e.toString())
                }
                handler.post {
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}